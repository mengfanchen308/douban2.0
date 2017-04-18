import requests
from comment.mysql_curd import *

ips = ['139.199.169.135:12345', '123.206.116.180:12345', '139.199.189.124:12345']
for ip in ips:
    try:
        result = requests.get('https://movie.douban.com/subject/25765735/comments?'
                              'start=0&limit=20&sort=new_score&status=P',
                              proxies={'https': ip})
        print(ip + 'can reach')
    except Exception as e:
        print(repr(e))
