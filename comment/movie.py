from comment.request_util import *
from comment.python3_rank import *
from lxml import etree
from gevent.queue import JoinableQueue
from gevent import monkey
import random
import gevent
monkey.patch_all(ssl=False)


class Movie(object):

    def __init__(self, movie_num, movie_name):
        self.num = movie_num
        self.name = movie_name
        self.comment_url = 'https://movie.douban.com/subject/' + self.num + '/comments?start={0}&limit=20&sort=new_score&status=P'
        self.comment_num_url = 'https://movie.douban.com/subject/' + self.num
        self.result = ''
        self.tool = MysqlCurd('douban_movie')
        self.tool.connect_mysql()

    def downloader(self, url, cookies=False, proxy=False):
        return super_downloader(url, cookies=cookies, proxy=proxy)

    def analysis_comment(self):
        page = etree.HTML(self.result)
        comments = page.xpath('//*[@id="comments"]')[0]
        for comment_item in comments.xpath('div[@class="comment-item"]'):
            param = {}
            info = comment_item.xpath('div[2]/h3/span[2]')[0]
            try:
                user_name = str(info.xpath('a')[0].text.encode('utf8'))
                param['user_name'] = user_name
            except IndexError:
                print('no user')
            try:
                score = int(info.xpath('span[2]')[0].get('class')[7:-8])  # 求星级
                param['score'] = score
                comment = comment_item.xpath('div[2]/p')[0].text
                param['comment'] = comment
            except Exception as e:
                print(e)
                print('this guy did not give his score or comment.')
                continue
            try:
                comment_time = info.xpath('span[@class="comment-time "]')[0].text.strip()
                vote = int(comment_item.xpath('div[2]/h3/span[1]/span')[0].text)
                param['comment_time'] = comment_time
                param['vote'] = vote
            except Exception as e:
                print(e)
                print('this comment no time no vote')
            self.tool.replace_mysql(self.name, param)
        self.tool.close_connect()

    def analysis_movie_info(self):
        try:
            page = etree.HTML(self.downloader(self.comment_num_url, cookies=True, proxy=True))
        except requests.exceptions.RequestException:
            print(self.name + 'info download error!')
            return False
        param = {'movie_name': self.name, 'movie_id': self.num}
        num = page.xpath('//*[@id="comments-section"]/div[1]/h2/span/a')
        param['comment_num'] = int(num[0].text.split(' ')[1])

        director_or_screen = {'导演': 'director', '编剧': 'screenwriter'}

        key = page.xpath('//*[@id="info"]/span[1]/span[@class="pl"]')[0].text
        value = director_or_screen.get(key)
        if value:
            param[value] = ''
            for d in page.xpath('//*[@id="info"]/span[1]/span[@class="attrs"]/a'):
                param[value] += d.text + ','

        key = page.xpath('//*[@id="info"]/span[2]/span[@class="pl"]')[0].text
        value = director_or_screen.get(key)
        if value:
            param[value] = ''
            for d in page.xpath('//*[@id="info"]/span[2]/span[@class="attrs"]/a'):
                param[value] += d.text + ','

        try:
            actors = page.xpath('//*[@id="info"]/span[@class="actor"]/span[2]')[0]
            param['actor'] = ''
            for _ in actors.xpath('a'):
                param['actor'] += _.text + ','
        except IndexError:
            pass

        mark = page.xpath('//*[@id="info"]')[0]
        param['type'] = ''
        for temp in mark.xpath('span[@property="v:genre"]'):
            param['type'] += temp.text + ','

        dates = page.xpath('//*[@id="info"]/span[@property="v:initialReleaseDate"]')
        param['date'] = ''
        for d in dates:
            param['date'] += d.text + ','

        mark = page.xpath('//*[@id="link-report"]//span[@property="v:summary"]')
        param['image'] = page.xpath('//*[@id="mainpic"]/a/img')[0].get('src')
        param['abstract'] = ''
        for temp in mark[0].xpath('text()'):
            param['abstract'] += temp.strip()

        score = page.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/strong')[0].text
        if score:
            param['score'] = float(score)

        try:
            self.tool.replace_mysql('movie_info', param)
            self.tool.close_connect()
            baidu_tool = MysqlCurd('douban_movie')
            baidu_tool.connect_mysql()
            baidu_tool.replace_mysql('name_id', {'movie_id': self.num, 'movie_name': self.name, 'version': 1})
            baidu_tool.close_connect()
        except Exception as e:
            print(e)


def get_movie_info(name=None):
    q = JoinableQueue()
    tool = MysqlCurd('douban_movie')
    tool.connect_mysql()
    if name:
        movie_id = tool.query_mysql_condition('name_id', [{'movie_name': name}, ['movie_id']])[0][0]
        if movie_id:
            q.put((movie_id, name))
        else:
            print('no id!')
    else:
        result = tool.query_mysql_condition('name_id', [{'version': 0}, ['movie_id', 'movie_name']])
        for temp in result:
            if not tool.query_mysql_condition('movie_info', [{'movie_id': temp[0]}, ['movie_name']]):
                q.put(temp)
    error_q = JoinableQueue()

    def temp(time):
        while not q.empty():
            data = q.get()
            m = Movie(data[0], data[1])
            try:
                m.analysis_movie_info()
                gevent.sleep(random.uniform(time[0], time[1]))
                print('analysis movie info ' + data[1] + 'completed!')  # 显示到控制台进行到哪个电影
            except Exception as e:
                print(e)
                print('analysis movie info ' + data[1] + 'error')
                error_q.put(data[1])
            print(len(q), 'remain!')
    worker = SleepFunction()
    worker.run(temp)
    with open('errorlist//movie_info.txt', 'a', encoding='utf8') as f:
        if not error_q.empty():
            print(get_time(), file=f)
            while not error_q.empty():
                print(error_q.get(), file=f)


def get_movie_comment(movie_name):
    tool = MysqlCurd('douban_movie')
    tool.connect_mysql()
    data = tool.query_mysql_condition('movie_info', [{'movie_name': movie_name}, ['movie_id', 'movie_name',
                                                                                  'comment_num']])[0]
    if data.__len__() == 0:
        print('dont have this movie id!')
        return False
    print(data[1] + ' started!' + str(data[2]) + 'comments!')
    m_table = Movie(data[0], data[1])
    m_table.tool.create_table(m_table.name, {'user_name': 'varchar(135) not null primary key',
                                             'score': 'int',
                                             'comment_time': 'varchar(45)',
                                             'vote': 'int',
                                             'comment': 'varchar(1000) not null'})
    comment_num = data[2]
    num_q = JoinableQueue()
    for i in range(0, comment_num, 20):
        num_q.put(str(i))

    def temp(time):
        while not num_q.empty():
            m = Movie(data[0], data[1])
            index = num_q.get()  # 非阻塞的
            try:
                m.result = m.downloader(m.comment_url.format(index), cookies=True, proxy=True)
            except requests.exceptions.RequestException:
                print(index + 'download error!')
            gevent.sleep(random.uniform(time[0], time[1]))
            try:
                m.analysis_comment()
                print(index + 'completed')
            except Exception as e:
                print(e)
                print(index + 'error')
            print(len(num_q))
    worker = SleepFunction()
    worker.run(temp)


def get_movie_id():
    baidu_tool = MysqlCurd('douban_movie')
    baidu_tool.connect_mysql()
    result = baidu_tool.query_mysql_condition('movie_name', [{'version': 0}, ['name']])
    q = JoinableQueue()
    for temp in result:
        if not baidu_tool.query_mysql_condition('name_id', [{'movie_name': temp[0]}, ['movie_id']]):
            q.put(temp[0])
    error_q = JoinableQueue()

    def crawl(time):
        while not q.empty():
            tool = MysqlCurd('douban_movie')
            tool.connect_mysql()
            name = q.get()
            try:
                page = super_downloader('https://movie.douban.com/subject_search?', params={'search_text': name},
                                        cookies=True, proxy=True)
            except requests.exceptions.RequestException:
                print('get movie id ' + name + 'download error!')
                return False
            page = etree.HTML(page)
            gevent.sleep(random.uniform(time[0], time[1]))
            try:
                count = 0
                for _ in page.xpath('//*[@id="content"]/div/div[1]/div[2]/table[@width="100%"]'):
                    try:
                        mark = _.xpath('tr/td[2]/div')[0]
                        id = mark.xpath('a')[0].get('href')[33:-1]
                        _name = mark.xpath('a')[0].text.split('/')[0].strip()
                        # score = mark.xpath('div/span[2]')[0].text
                        # comment_num = mark.xpath('div/span[3]')[0].text[1:-4]
                        tool.replace_mysql('name_id', {'movie_id': id, 'movie_name': _name})
                    except IndexError:
                        continue
                    count += 1
                    if count == 3:
                        break
                tool.close_connect()
                own_tool = MysqlCurd('douban_movie')
                own_tool.connect_mysql()
                own_tool.replace_mysql('movie_name', {'version': 1, 'name': name})
                own_tool.close_connect()
                print('get movie id ' + name + ' completed!')
            except Exception as e:
                error_q.put(name)
                print('get movie id ' + name + ' error!')
                print(e)
    worker = SleepFunction()
    worker.run(crawl)
    with open('errorlist//movie_id.txt', 'a', encoding='utf8') as f:
        if not error_q.empty():
            print(get_time(), file=f)
            while not error_q.empty():
                print(error_q.get(), file=f)
