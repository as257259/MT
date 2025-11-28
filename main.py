import json
import requests
import re
import os
import time
import random

s = set()
ip = ""
total_retry_count = 0
MAX_RETRY = 3
Retry = {}
accounts_list = {}



headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

s.add('111.22.7.195:8008')
s.add('121.237.181.137:8888')
s.add('36.136.27.2:4999')
s.add('42.180.0.58:6182')
s.add('36.110.143.55:8080')
s.add('221.217.54.145:9000')
s.add('123.128.12.93:9050')
s.add('220.197.44.36:3128')
s.add('120.92.211.211:7890')
s.add('222.129.137.95:9000')
s.add('112.111.13.253:7890')
s.add('14.103.233.245:3128')
s.add('61.169.156.182:8118')
s.add('222.59.173.105:45167')
s.add('221.226.132.162:10081')
s.add('58.249.55.222:9797')
s.add('36.147.78.166:80')
s.add('117.186.78.226:18080')
s.add('1.85.33.94:6666')
s.add('210.75.240.135:10044')
s.add('202.112.51.124:3128')
s.add('222.59.173.105:45123')
s.add('39.185.41.193:5911')
s.add('1.94.145.211:8989')
s.add('120.92.212.16:7890')
s.add('139.159.97.42:9798')
s.add('36.129.129.215:9000')
s.add('123.112.244.220:9000')

def verify():
    global ip
    target_url = 'https://bbs.binmt.cc/forum.php?mod=guide&view=hot'
    max_attempts = min(len(s), 100)
    attempt_count = 0
    while s and attempt_count < max_attempts:
        attempt_count += 1
        if not s:
            break
        proxy = random.choice(list(s))
        print(f"{attempt_count}: {proxy}", end="\r")
        proxies = {
            'https': f'http://{proxy}',
            'http': f'http://{proxy}'
        }
        try:
            response = requests.get(target_url, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                print(f"{attempt_count}: {proxy}", "✔")
                ip = proxy
                s.remove(proxy)
                return
        except Exception as e:
            pass
        s.remove(proxy)
        print(f"{attempt_count}: {proxy}", "✖")
        time.sleep(0.1)

def checkIn(user, pwd):
    req = requests.session()
    req.headers.update(headers)
    proxies = {
        'http': f'http://{ip}',
        'https': f'http://{ip}'
    }
    req.proxies = proxies
    print(user, "开始签到")
    try:
        url = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
        resp = req.get(url, proxies=proxies, timeout=10)
        resp.encoding = resp.apparent_encoding
        if resp.ok:
            content = resp.text
            _loginhash = loginhash(content)
            _formhash = formhash(content)
            url = f'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={_loginhash}&inajax=1'
            data = {
                'formhash': _formhash,
                'referer': 'https://bbs.binmt.cc/k_misign-sign.html',
                'fastloginfield': 'username',
                'username': user,
                'password': pwd,
                'questionid': '0',
                'answer': '',
                'agreebbrule': ''
            }
            resp = req.post(url, data=data, proxies=proxies, timeout=10)
            resp.encoding = resp.apparent_encoding
            if resp.ok:
                if '失败' in resp.text:
                    print("密码错误")
                    return
                url = 'https://bbs.binmt.cc/k_misign-sign.html'
                resp = req.get(url, proxies=proxies, timeout=10)
                resp.encoding = resp.apparent_encoding
                _formhash = formhash(resp.text)
                code = resp.status_code
                if resp.ok:
                    url = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={_formhash}'
                    resp = req.get(url, proxies=proxies, timeout=10)
                    resp.encoding = resp.apparent_encoding
                    print(CDATA(resp.text))
                    if '已签' in resp.text:
                        del accounts_list[user]
    except Exception as e:
        print(f"异常{str(e)}")
        Retry[user] = pwd

def loginhash(data):
    pattern = r'loginhash.*?=(.*?)[\'"]>'
    match = re.search(pattern, data, re.IGNORECASE | re.UNICODE)
    if match and match.group(1):
        return match.group(1).strip()
    return ''

def formhash(data):
    pattern = r'formhash[\'"].*?value=[\'"](.*?)[\'"].*?/>'
    match = re.search(pattern, data, re.IGNORECASE | re.UNICODE)
    if match and match.group(1):
        return match.group(1).strip()
    return ''

def CDATA(data):
    pattern = r'CDATA.*?(.*?)]>'
    match = re.search(pattern, data, re.IGNORECASE | re.UNICODE)
    if match and match.group(1):
        return match.group(1).strip('[]')
    return ''
        
def start():
    global Retry, total_retry_count
    if Retry and total_retry_count < MAX_RETRY:
        total_retry_count += 1
        for key, value in Retry.items():
            accounts_list[key] = value
        Retry.clear()
    if accounts_list:
        verify()
        if not ip: return
        keys = list(accounts_list.keys())
        total = len(keys)
        for i, username in enumerate(keys):
            checkIn(username, accounts_list[username])
            if i < total - 1:
                time.sleep(3)
        start()

if 'mtluntan' in os.environ:
    fen = os.environ.get("mtluntan", "").split(",")
    for duo in fen:
        if ':' not in duo:
            continue
        username, password = pair.split(':', 1)
        username = username.strip()
        password = password.strip()
        if username and password:
            accounts_list[username] = password
    start()
else:
    print('github变量未设置')    