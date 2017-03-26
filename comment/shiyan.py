from comment.mysql_curd import *
import requests
from lxml import etree
from comment.request_util import *
super_downloader('https://movie.douban.com/subject/25765735/comments?start=40200&limit=20&sort=new_score&status=P', cookies=True, proxy=True)