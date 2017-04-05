from gevent.queue import JoinableQueue
from comment.python3_rank import *
from comment.request_util import *

monkey.patch_all(ssl=False)


users = config.get('need', 'users')
users = users.split(',')
proxy = eval(config.get('proxy', 'ip'))
user_agents = eval(config.get('header', 'user_agent'))


def get_person_info():
    baidu_tool = MysqlCurd('douban_person')
    baidu_tool.connect_mysql()
    result = baidu_tool.query_mysql_condition('person_name_id', [{'version': 0}, ['person_id', 'person_name']])
    print(result)
    print(result.__len__())
    q = JoinableQueue()
    for _ in result:
        if not baidu_tool.query_mysql_condition('person_info', [{'person_id': _[0]}, ['person_name']]):
            q.put(_)
    error_q = JoinableQueue()
    baidu_tool.close_connect()

    def temp(param):
        while not q.empty():
            i = q.get()
            p = Person(id=i[0], name=i[1])
            flag = p.analysis_person_info()
            if flag:
                name_id_tool = MysqlCurd('douban_person')
                name_id_tool.connect_mysql()
                name_id_tool.replace_mysql('person_name_id',
                                           {'person_id': p.id, 'person_name': p.name, 'version': 1})
                name_id_tool.close_connect()
            else:
                error_q.put((p.id, p.name))
    worker = SleepFunction()
    worker.run(temp)
    with open('errorlist//person_id.txt', 'a', encoding='utf8') as f:
        if not error_q.empty():
            print(get_time(), file=f)
            while not error_q.empty():
                print(error_q.get(), file=f)


def get_person_id():
    baidu_tool = MysqlCurd('douban_person')
    baidu_tool.connect_mysql()
    result = baidu_tool.query_mysql_condition('person_name', [{'version': 0}, ['name']])
    print(result)
    print(result.__len__())
    q = JoinableQueue()
    for _ in result:
        if not baidu_tool.query_mysql_condition('person_name_id', [{'person_name': _[0]}, ['person_id']]):
            q.put(_[0].strip('\n'))
    error_q = JoinableQueue()

    def crawl(param):
        while not q.empty():
            tool = MysqlCurd('douban_person')
            tool.connect_mysql()
            name = q.get()
            try:
                result = super_downloader('https://movie.douban.com/subject_search?',
                                          params={'search_text': name}, proxy=True,cookies=True)
                gevent.sleep(random.uniform(2, 6.5))
            except requests.exceptions.RequestException as e:
                print(name + 'download error!')
                continue
            try:
                page = etree.HTML(result)
                basic = page.xpath('//*[@id="content"]/div/div[@class="article"]/div[1]/'
                                   'div[@class="result-item"]/div[@class="content"]/h3/a')[0]
                id = basic.get('href')[35:-1]
                name = basic.text.split()[0]
                tool.replace_mysql('person_name_id', {'person_id': id, 'person_name': name, })
                baidu_tool = MysqlCurd('douban_person')
                baidu_tool.connect_mysql()
                baidu_tool.replace_mysql('person_name', {'name': name, 'version': 1})
                baidu_tool.close_connect()
                tool.close_connect()
                print(name+'completed')
            except IndexError:
                error_q.put(name)
                print(name + 'error!')

    worker = SleepFunction()
    worker.run(crawl)
    with open('errorlist//person_id.txt', 'a', encoding='utf8') as f:
        if not error_q.empty():
            print(get_time(), file=f)
            while not error_q.empty():
                print(error_q.get(), file=f)



class Person:

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.url = 'https://movie.douban.com/celebrity/' + self.id
        self.awards_url = 'https://movie.douban.com/celebrity/' + self.id + '/awards/'
        self.works_url = 'https://movie.douban.com/celebrity/' + self.id + \
                         '/movies?start={0}&format=pic&sortby=time&'
        self.works_url_quick = 'https://movie.douban.com/celebrity/' + self.id + \
                               '/movies?start={0}&format=text&sortby=time&'
        self.keywords = {'性别': 'sex',
                         '星座': 'constellation',
                         '出生日期': 'birthday',
                         '出生地': 'homeplace',
                         '更多外文名': 'foreign_name',
                         '更多中文名': 'chinese_name',
                         '职业': 'occupation'
                         }
        self.param = {'person_id': self.id}
        self.tool = MysqlCurd('douban_person')
        self.tool.connect_mysql()

    def downloader(self, url, cookies=False, proxy=False):
        return super_downloader(url, cookies=cookies, proxy=proxy)

    def analysis_person_info(self):
        try:
            result = self.downloader(self.url, cookies=True, proxy=True)
            page = etree.HTML(result)
            self.name = page.xpath('//*[@id="content"]/h1')[0].text.split()[0]
            self.param['person_name'] = self.name
            mark = page.xpath('//*[@id="headline"]/div[@class="info"]/ul')[0]
        except Exception as e:
            print(e)
            print(self.name + 'info download error!')
            return False
        try:
            image = page.xpath('//*[@id="headline"]/div[@class="pic"]/a/img')[0].get('src')
            self.param['image'] = image
        except Exception as e:
            print(self.name + 'no picture!')
        for temp in mark.xpath('li'):
            try:
                keyword = temp.xpath('span')[0].text
                column = self.keywords.get(keyword)
                if column == None:
                    continue
                else:
                    self.param[column] = temp.xpath('text()')[1].replace('\n', '').\
                        replace('    ', '').replace(':', '').strip()
                    #没办法就是很复杂
            except IndexError:
                continue
        try:
            abstract = page.xpath('//*[@id="intro"]/div[@class="bd"]')[0].text.strip()
            if abstract == '':
                abstract = page.xpath('//*[@id="intro"]/div[@class="bd"]/span[@class="short"]')[0].text.strip()
                try:
                    long_abstract = page.xpath('//*[@id="intro"]/div[@class="bd"]/span[@class="all hidden"]/text()')
                    l_ab = ''
                    for _ in long_abstract:
                        l_ab += _.strip()
                    self.param['long_abstract'] = l_ab
                except IndexError:
                    pass
            self.param['abstract'] = abstract
        except IndexError:
            pass
        self.tool.replace_mysql('person_info', self.param)
        self.tool.close_connect()
        print('analysis person info: ' + self.name + 'finished!')
        return True

    def analysis_person_award(self):
        try:
            result = self.downloader(self.awards_url, cookies=True, proxy=True)
            page = etree.HTML(result)
            article = page.xpath('//*[@id="content"]/div/div[@class="article"]')[0]
        except IndexError and requests.exceptions.RequestException:
            print(self.name + 'award download error!')
            return False
        self.tool.create_table(self.name + '_awards', {'date': 'varchar(45) not null',
                                                       'id': 'int auto_increment primary key not null',
                                                       'award_name': 'varchar(150) not null',
                                                       'award_prize': 'varchar(150) not null',
                                                       'award_movie': 'varchar(150) '})
        for awards in article.xpath('div[@class="awards"]'):
            try:
                date = awards.xpath('div[@class="hd"]/h2')[0].text
                for award in awards.xpath('ul[@class="award"]'):
                    award_name = award.xpath('li[1]/a')[0].text
                    award_prize = award.xpath('li[2]')[0].text
                    award_movie = award.xpath('li[3]/a')[0].text
                    self.tool.replace_mysql(self.name + '_awards', {'date': date,
                                                                    'award_name': award_name,
                                                                    'award_prize': award_prize,
                                                                    'award_movie': award_movie})
            except IndexError:
                continue
        print('analysis person award: ' + self.name + 'finished!')
        return True

    def analysis_person_works_quick(self):
        self.tool.create_table_force(self.name + '_works', {'date': 'int not null',
                                                            'movie_name': 'varchar(100) not null',
                                                            'movie_id': 'varchar(45) not null primary key',
                                                            'part': 'varchar(45) default null',
                                                            'score': 'decimal(2,1) default null'
                                                            })
        # 'comments_num': 'int default null'

        def analysis(page):
            tbody = page.xpath('//*[@id="content"]/div/div[@class="article"]/div[@class="list_view"]/table/tbody')[0]
            for tr in tbody.xpath('tr'):
                try:
                    movie_name = tr.xpath('td[@headers="m_name"]/a')[0].text
                    movie_id = tr.xpath('td[@headers="m_name"]/a')[0].get('href').split('/')[4]
                    part = tr.xpath('td[@headers="mc_role"]')[0].text
                    date = tr.xpath('td[@headers="mc_date"]')[0].text
                    try:
                        score = float(tr.xpath('td[@headers="mc_rating"]/div/span[@class="rating_nums"]')[0].text)
                        self.tool.replace_mysql(self.name + '_works', {'date': date,
                                                                       'movie_id': movie_id,
                                                                       'movie_name': movie_name,
                                                                       'part': part,
                                                                       'score': score})
                    except:
                        self.tool.replace_mysql(self.name + '_works', {'date': date,
                                                                       'movie_id': movie_id,
                                                                       'movie_name': movie_name,
                                                                       'part': part})
                except IndexError:
                    continue
        index = 0
        try:
            result = self.downloader(self.works_url_quick.format(index), cookies=True, proxy=True)
            page = etree.HTML(result)
            num = int(page.xpath('//*[@id="content"]/h1')[0].text.split('的全部作品')[1][1:-1])
        except IndexError and requests.exceptions.RequestException:
            print(self.name + 'work download error!')
            return False
        analysis(page)
        for index in range(25, num, 25):
            try:
                page = etree.HTML(self.downloader(self.works_url.format(index), cookies=True, proxy=True))
                analysis(page)
            except requests.exceptions.RequestException:
                continue
        print('analysis person word quick: ' + self.name + 'finished!')
        return True

    def analysis_person_work(self):
        '''
        自动请求不需要额外请求
        :return:
        '''
        self.tool.create_table(self.name + '_works', {'date': 'int not null',
                                                      'movie_name': 'varchar(100) not null',
                                                      'movie_id': 'varchar(45) not null primary key',
                                                      'part': 'varchar(45) default null',
                                                      'score': 'decimal(2,1) default null',
                                                      'comments_num': 'int default null'})
        index = 0
        while True:
            try:
                result = self.downloader(self.works_url.format(index), cookies=True, proxy=True)
                page = etree.HTML(result)
                ul = page.xpath('//*[@id="content"]/div/div[@class="article"]/div[@class="grid_view"]/ul')[0]
            except IndexError and requests.exceptions.RequestException:
                print(self.name + 'work download error!')
                return False
            for li in ul.xpath('li'):
                try:
                    mark = li.xpath('dl/dd/h6')[0]
                    movie_id = int(mark.xpath('a')[0].get('href').split('/')[4])
                    movie_name = mark.xpath('a')[0].text
                    date = int(mark.xpath('span[1]')[0].text[1:-1])
                    part = mark.xpath('span[2]')[0].text.strip('[]').strip()
                    try:
                        mark = li.xpath('dl/dd/div[@class="star clearfix"]')[0]
                        comments_num = int(mark.xpath('span[3]')[0].text[:-3])
                        score = float(mark.xpath('span[2]')[0].text)
                        self.tool.replace_mysql(self.name + '_works', {'date': date,
                                                                       'movie_id': movie_id,
                                                                       'movie_name': movie_name,
                                                                       'part': part,
                                                                       'score': score,
                                                                       'comments_num': comments_num
                                                                       })
                    except IndexError:
                        self.tool.replace_mysql(self.name + '_works', {'date': date,
                                                                       'movie_id': movie_id,
                                                                       'movie_name': movie_name,
                                                                       'part': part})
                except IndexError:
                    continue

            try:
                if page.xpath('//*[@id="content"]/div/div[1]/div[3]/span[3]')[0].text.strip() == '后页>':
                    break
            except IndexError:
                break
            index += 10
        print('analysis person work: ' + self.name + 'finished!')
        return True

if __name__ == '__main__':
    tool = MysqlCurd('douban_person')
    tool.connect_mysql()
    persons = tool.query_mysql_condition('person_info', [{'version': 0}, ['person_name', 'person_id']])
    print(persons)
    print(persons.__len__())
    q = JoinableQueue()
    for _ in persons:
        q.put(_)

    def temp(param):
        while not q.empty():
            i = q.get()
            p = Person(id=i[1], name=i[0])

            flag = p.analysis_person_info()
            if flag:
                name_id_tool = MysqlCurd('douban_person')
                name_id_tool.connect_mysql()
                name_id_tool.replace_mysql('person_name_id',
                                          [{'person_id': p.id, 'person_name': p.name, 'version': 0}])
                name_id_tool.close_connect()

            # p.analysis_person_award()

            flag = p.analysis_person_works_quick()
            if flag:
                douban_tool = MysqlCurd('douban_person')
                douban_tool.connect_mysql()
                douban_tool.update_mysql('person_info', [{'person_id': i[1]}, {'version': 1}])
                douban_tool.close_connect()
            gevent.sleep(random.uniform(1, 5))
    workers = []
    for i in range(0, 20):
        workers.append(gevent.spawn(temp, 'worker'))
    try:
        gevent.joinall(workers)
    except gevent.hub.LoopExit:
        pass
