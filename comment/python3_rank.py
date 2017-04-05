import json

import requests
from gevent import monkey
from gevent.pool import Pool

from comment.objects.mysql_curd import MysqlCurd

monkey.patch_all(ssl=False)

class myspider:

    def __init__(self, param):
        self.param = param#用于存储表名，url信息，数据库信息
        self.data = {}#用于存储接受的json数据块
        self.result = []#处理好的data

    def downloader(self, url='http://top.baidu.com/detail/list'):
        data = requests.get(url, params=self.param)
        self.data = json.loads(data.text)
        return self.data

    def analysis(self):
        data = []
        for onething in self.data['list']:
            temp = {}
            temp['name'] = onething['keyword']
            temp['rank'] = onething['searches']
            data.append(temp)
        self.result = data
        return self.result

    def store_mysql(self):
        tool = MysqlCurd('baidu_rank')#传入数据库名字参数建立连接
        tool.connect_mysql()
        tool.create_table(self.param['name'], {'name': 'varchar(20) not null primary key', 'rank': 'varchar(20) not null'})
        for _ in self.result:
            tool.replace_mysql(self.param['name'], _)
        tool.conn.commit()
        tool.close_connect()


def get_baidu_rank(param):
    bs = param

    def temp(bs):
        spider = myspider(bs)
        spider.downloader()
        spider.analysis()
        spider.store_mysql()

    pool = Pool(20)
    pool.map(temp, bs)

if __name__ == '__main__':
    bs = [{'name': 'comic', 'boardid': '23'},
          {'name': 'hot_person', 'boardid': '258'},
          {'name': 'baidu_movie', 'boardid': '26'},
          {'name': 'baidu_tv', 'boardid': '4'}]
    get_baidu_rank(bs)

    # print(pool.map(analysis, result))
    # bs = [{'name': 'comic', 'boardid': '23'},
    #       {'name': 'hot_person', 'boardid': '258'},
    #       {'name': 'baidu_movie', 'boardid': '26'},
    #       {'name': 'baidu_tv', 'boardid': '4'}]
    # get_baidu_rank(bs)

