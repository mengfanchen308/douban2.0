from comment.person import *
from comment.movie import *
import sys

monkey.patch_all(ssl=False)


def main(argv):
    if argv[1] == 'getcookie':
        users = config.get('need', 'users')
        users = users.split(',')
        print(users)
        for user in users:
            get_cookie(user)
        exit(0)
    elif argv[1] == 'shell':
        f = open('namelist', 'r', encoding='utf8')
        f.readline()
        name = f.readline().strip()
        print('开始对' + name + '进行操作')
        if name == 'movie':
            if argv[2]:
                cmd = argv[2]
            else:
                cmd = input('1:get_movie_id  2:get_movie_info  3:get_movie_comments\n')
            if cmd == '1':
                mysql_tool = MysqlCurd('douban_movie')
                mysql_tool.connect_mysql()
                for line in f:
                    if not line.strip() == '' \
                            and not mysql_tool.query_mysql_condition('movie_name', [{'name': line.strip()},
                                                                                    ['name']]):
                        mysql_tool.insert_mysql('movie_name', {'name': line.strip()})
                    elif not line.strip() == '':
                        print('already have this movie.' + line.strip())
                # 将名单存好
                for _ in range(0, 1):
                    get_movie_id()
                    print('过滤第' + str(_) + '次!')
                mysql_tool.delete_mysql('movie_name', {'version': 0})
                mysql_tool.close_connect()

            elif cmd == '2':
                print('首先获取所有电影的id')
                mysql_tool = MysqlCurd('douban_movie')
                mysql_tool.connect_mysql()
                for line in f:
                    if not line.strip() == '' \
                            and not mysql_tool.query_mysql_condition('movie_name', [{'name': line.strip()},
                                                                                    ['name']]):
                        mysql_tool.insert_mysql('movie_name', {'name': line.strip()})
                # 将名单存好
                for _ in range(0, 1):
                    get_movie_id()
                    print('过滤第' + str(_) + '次!')
                mysql_tool.delete_mysql('movie_name', {'version': 0})
                print('获得所有电影信息')
                for _ in range(0, 1):
                    get_movie_info()
                    print('过滤第' + str(_) + '次!')
                mysql_tool.delete_mysql('name_id', {'version': 0})
                mysql_tool.close_connect()

            elif cmd == '3':
                for line in f:
                    if not line.strip() == '':
                        get_movie_info(line.strip())
                        get_movie_comment(line.strip())

        elif name == 'person':
            cmd = input('1:get_person_id  2:get_person_info\n')
            if cmd == '1':
                mysql_tool = MysqlCurd('douban_person')
                mysql_tool.connect_mysql()
                for line in f:
                    if not line.strip() == '':
                        mysql_tool.insert_mysql('person_name', {'name': line.strip()})
                # 将名单存好
                for _ in range(0, 2):
                    get_person_id()
                    print('过滤第' + str(_) + '次!')
                mysql_tool.delete_mysql('person_name', {'version': 0})
                mysql_tool.close_connect()
            elif cmd == '2':
                print('首先获取所有人物的id')
                mysql_tool = MysqlCurd('douban_person')
                mysql_tool.connect_mysql()
                for line in f:
                    if not line.strip() == '':
                        mysql_tool.insert_mysql('person_name', {'name': line.strip()})
                # 将名单存好
                for _ in range(0, 2):
                    get_person_id()
                    print('过滤第' + str(_) + '次!')
                mysql_tool.delete_mysql('person_name', {'version': 0})

                for _ in range(0, 2):
                    get_person_info()
                    print('过滤第' + str(_) + '次!')
                mysql_tool.delete_mysql('person_name_id', {'version': 0})
        else:
            print('请在namelist中更改类型')
            exit(0)
    else:
        print('please input your command')
    exit(0)


if __name__ == '__main__':
    main(sys.argv)
    print('there are some changes')
