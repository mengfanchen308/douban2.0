import requests
import gevent
from lxml import etree
import configparser
import http.cookiejar
import urllib.request
from comment.mysql_curd import MysqlCurd
import random
from gevent import monkey
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
monkey.patch_all(ssl=False)

config = configparser.ConfigParser()
config.read('config.ini')
users = config.get('need', 'users')
users = users.split(',')
proxies = eval(config.get('proxy', 'ip'))
user_agents = eval(config.get('header', 'user_agent'))


class SleepFunction(object):
    worker_num = 20
    time = (1, 5)

    @classmethod
    def run(cls, func):
        workers = []
        for i in range(0, SleepFunction.worker_num):
            workers.append(gevent.spawn(func, SleepFunction.time))
        try:
            gevent.joinall(workers)
        except Exception as e:
            pass


def super_downloader(url, referer='https://movie.douban.com/', cookies=False, proxy=False, params=None, timeout=5):
    header = {'Referer': referer,
              'User-Agent': random.choice(user_agents)}
    if not cookies and not proxy:
        page = requests.get(url, headers=header, params=params, timeout=timeout)
        return page.text

    elif cookies and proxy:
        s = requests.Session()
        s.headers = header
        cookie_jar = http.cookiejar.LWPCookieJar()
        cookie_jar.load(users[random.randint(0, len(users) - 1)] + '.txt', ignore_discard=True, ignore_expires=True)
        cookie_dic = requests.utils.dict_from_cookiejar(cookie_jar)
        s.cookies = requests.utils.cookiejar_from_dict(cookie_dic)
        proxy_use = random.choice(proxies)
        page = s.get(url, headers=header,
                     cert=False,
                     params=params,
                     proxies={'https': proxy_use, 'http': proxy_use},
                     timeout=timeout)
        return page.text

    elif proxy and not cookies:
        s = requests.Session()
        s.headers = header
        proxy_use = random.choice(proxies)
        page = s.get(url, headers=header, cert=False, proxies={'https': proxy_use, 'http': proxy_use}, timeout=timeout)
        return page.text


def get_cookie(account):
    temp = requests.get('https://accounts.douban.com/login')
    page = etree.HTML(temp.text)
    config = configparser.ConfigParser()
    config.read('config.ini')
    postdata = {'form_email': config.get(account, 'account'),
                'form_password': config.get(account, 'password'),
                'login': '登陆'}
    try:
        #  此处try是因为有时会没有验证码
        image_id = page.xpath('//*[@id="captcha_image"]')[0].attrib['src']
        urllib.request.urlretrieve(image_id, 'verify.jpg')
        # image_email('verify.jpg')
        image = input('input the verify image!')  # 输入验证码
        image_id = image_id.split('&')[0].replace('https://www.douban.com/misc/captcha?id=', '')  # 验证码图片信息
        postdata['captcha-solution'] = image
        postdata['captcha-id'] = image_id
    except Exception as e:
        print(e)
        pass

    header = {'Referer': 'https://www.douban.com/',
              'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0'}
    sess = requests.Session()
    sess.cookies = http.cookiejar.LWPCookieJar(account + '.txt')
    result = sess.post('https://accounts.douban.com/login', data=postdata, headers=header)
    print(result.url)
    if not result.url == 'https://www.douban.com/':
        print(account + 'error')
    else:
        sess.cookies.save(ignore_discard=True, ignore_expires=True)
        print(account + 'completed')
    '''
    cookie_dict = {c.name: c.value for c in sess.cookies}#处理cookie为字典型
    requests.utils.cookiejar_from_dict(cookie_dict, cookie_jar)
    cookie_jar.save(account + '.txt',ignore_discard=True, ignore_expires=True)
    return sess#返回sess是将其直接用于请求链接其中已经包含cookie无需加载cookie文本文件
    '''


def image_email(image):
    mail_user = "1034406291@qq.com"  # 用户名
    mail_pass = "yszuerescwhybbca"
    sender = '1034406291@qq.com '
    receivers = ['1034406291@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

    message = MIMEMultipart('alternative')
    message['From'] = '1034406291@qq.com'
    message['To'] = '1034406291@qq.com'
    message['Subject'] = 'Python SMTP 邮件测试'

    mail_msg = """
    <p>Python 邮件发送测试...</p>
    <p>验证码图片：</p>
    <p><img src="cid:image1"></p>
    """
    message.attach(MIMEText(mail_msg, 'html', 'utf-8'))

    file = open(image, 'rb')
    pic = MIMEImage(file.read())
    pic.add_header('Content-ID', '<image1>')
    message.attach(pic)

    try:
        smtpObj = smtplib.SMTP_SSL('smtp.qq.com', 465)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException as e:
        print(e)


def get_time():
    return datetime.datetime.now().strftime('%b-%d-%y %H:%M:%S')

if __name__ == '__main__':
    '''
    以下为加载所有配置文件中配置的账户cookie
    '''
    config = configparser.ConfigParser()
    config.read('config.ini')
    users = config.get('need', 'users')
    users = users.split(',')
    print(users)
    for user in users:
        get_cookie(user)
