import pymysql
import configparser
from comment.config import *


host = config.get('mysql_ip', 'ip')
user = config.get('mysql_ip', 'user')
password = config.get('mysql_ip', 'password')


class MysqlCurd:
    def __init__(self, database):
        self.db = database

    def connect_mysql(self):
        try:
            self.conn = pymysql.connect(host=host, user=user, password=password, db=self.db, charset='utf8', port=3306)
            self.curor = self.conn.cursor()
        except Exception as e:
            print(e)

    # def change_version(self, table):
    #     sql = 'update {0} set version=1'.format(table)
    #     try:
    #         self.curor.execute(sql)
    #         self.conn.commit()
    #     except Exception as e:
    #         print(e)

    def delete_mysql(self, table, param):
        """
        :param table: 表名字
        :param param: {条件}
        :return:
        """
        sql = 'delete from `{0}` where '.format(table)
        value = []
        for key in param.keys():  # condition 就是key
            sql += key + ' = %s and '
            value.append(param.get(key))
        sql = sql[:-4]
        try:
            self.curor.execute(sql, value)
            self.conn.commit()
        except Exception as e:
            print(e)

    def update_mysql(self, table, param):
        """
        完成任务为将某个表的某一行数据进行更新，主键为数组第一个键值对。其余为需要更改的信息
        update_mysql('short_comment_num', [{'movie_name': 'shiyan'},{'comment_num':'2700'}])
        :param table:
        :param param:
        :return:
        """
        sql = 'update ' + table + ' set '
        value = []
        for key in param[1].keys():
            sql += key + ' = %s,'
            value.append(param[1].get(key))
        sql = sql[:-1]
        sql += ' where '
        for key in param[0].keys():  # condition 就是key
            sql += key + ' = %s and '
            value.append(param[0].get(key))
        sql = sql[:-4]
        try:
            self.curor.execute(sql, value)
            self.conn.commit()
        except Exception as e:
            print(e)

    def replace_mysql(self, table, param):
        """
        param为数组，数组元素为dict，键为数据库列明，值为数据
        :param table:str
        :param param:{}
        :return:
        """
        value = []  # 用于存储所有参数
        sql = 'replace into ' + table + ' ('
        for key in param.keys():
            sql += key + ','
            value.append(param.get(key))
        sql = sql[:-1]
        sql += ') values (' + '%s,' * value.__len__()  # 确定传入参数个数
        sql = sql[:-1]
        sql += ')'
        try:
            self.curor.execute(sql, value)
            self.conn.commit()
        except Exception as e:
            print(sql)
            print(e)

    def insert_mysql(self, table, param):
        """
        param为数组，数组元素为dict，键为数据库列明，值为数据
        :param table:str
        :param param:{}
        :return:
        """
        value = []  # 用于存储所有参数
        sql = 'insert into `' + table + '` ('
        for key in param.keys():
            sql += key + ','
            value.append(param.get(key))
        sql = sql[:-1]
        sql += ') values (' + '%s,' * value.__len__()  # 确定传入参数个数
        sql = sql[:-1]
        sql += ')'
        try:
            self.curor.execute(sql, value)
            self.conn.commit()
        except Exception as e:
            print(sql)
            print(e)

    def query_mysql(self, table, param):
        """
        param = [{要查询的}]
        :param table:
        :param param:
        :return:
        """
        sql = 'select '
        for key in param:
            sql += key + ','
        sql = sql[:-1]
        sql += ' from `' + table + '`'
        try:
            self.curor.execute(sql)
            return self.curor.fetchall()
        except Exception as e:
            print(type(e))

    def query_mysql_condition(self, table, param):
        """
        param = [{条件},[查询]]
        :param table:
        :param param:
        :return:
        """
        sql = 'select '
        for key in param[1]:
            sql += key + ','
        sql = sql[:-1]
        sql += ' from `' + table + '` where '
        value = []
        for key in param[0].keys():
            sql += key + ' = %s and '
            value.append(param[0].get(key))
        sql = sql[:-4]
        try:
            self.curor.execute(sql, value)
            return self.curor.fetchall()
        except Exception as e:
            print(e)

    def create_table(self, table, param):
        """
        param是数组字典型存的是列名和属性，会删除原来同名表
        create table shiyan (id int not null auto_increment primary key , name varchar(20) not null , time timestamp default current_timestamp)
        :param table:
        :param param:
        :return:
        """
        sql = 'create table if not exists `' + table + '` ('
        for key in param.keys():
            sql += key + ' ' + str(param.get(key)) + ', '
        sql += 'time timestamp default current_timestamp)character set utf8 collate utf8_general_ci;'
        try:
            self.curor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(sql)
            print(e)

    def create_table_force(self, table, param):
        """
        param是数组字典型存的是列名和属性，会删除原来同名表
        create table shiyan (id int not null auto_increment primary key , name varchar(20) not null , time timestamp default current_timestamp)
        :param table:
        :param param:
        :return:
        """
        sql = 'drop table if exists ' + table + ';create table ' + table + ' ('
        for key in param.keys():
            sql += key + ' ' + str(param.get(key)) + ', '
        sql += 'time timestamp default current_timestamp)character set utf8 collate utf8_general_ci;'
        try:
            self.curor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(e)

    def close_connect(self):
        self.curor.close()
        self.conn.close()


if __name__ == '__main__':
    pass
