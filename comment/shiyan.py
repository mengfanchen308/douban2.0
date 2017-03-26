from comment.mysql_curd import *
import requests
from lxml import etree
from comment.request_util import *
result = requests.get('https://movie.douban.com/subject/25765735/comments?start=0&limit=20&sort=new_score&status=P',
             proxies={'https':'182.254.140.100:12345'}, timeout=5)
print(result.text)