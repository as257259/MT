import json, requests, re, os, time, random, ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from preferences import prefs
from logger import logger

IP_LIST = {}
accounts_list = {}
hasE = False
sign_fail = 0
RESULT_OK, RESULT_SKIP, RESULT_FAIL, RESULT_PWDERR = [], [], [], []
SENDKEY = os.environ.get('SENDKEY', '')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

ACW_KEY = None
ACW_B64 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/='
ACW_ARR = [0xf,0x23,0x1d,0x18,0x21,0x10,0x1,0x26,0xa,0x9,0x13,0x1f,0x28,0x1b,0x16,0x17,0x19,0xd,0x6,0xb,0x27,0x12,0x14,0x8,0xe,0x15,0x20,0x1a,0x2,0x1e,0x7,0x4,0x11,0x5,0x3,0x1c,0x22,0x25,0xc,0x24]
ACW_FALLBACK = '3000176000856006061501533003690027800375'


def acw_decode(s):
    out = bytearray()
    bits = 0
    nb = 0
    for ch in s:
        if ch == '=':
            break
        v = ACW_B64.find(ch)
        if v < 0:
            continue
        bits = (bits << 6) | v
        nb += 6
        while nb >= 8:
            nb -= 8
            out.append((bits >> nb) & 0xff)
    return out.decode('utf-8', 'ignore')


def acw_key(html):
    global ACW_KEY
    if ACW_KEY:
        return ACW_KEY
    m = re.search(r"function a0i\(\)\{var N=\[(.*?)\];", html, re.S)
    if m:
        for s in re.findall(r"'([^']*)'", m.group(1)):
            d = acw_decode(s)
            if len(d) == 40 and re.match(r'^[0-9a-fA-F]{40}$', d):
                ACW_KEY = d
                logger.info('WAF KEY 动态提取成功')
                return d
    ACW_KEY = ACW_FALLBACK
    return ACW_KEY


def acw_solve(html):
    m = re.search(r"arg1='([0-9A-Fa-f]{40})'", html)
    if not m:
        return None
    arg1 = m.group(1)
    pm = re.search(r"for\(var m=\[([^\]]+)\]", html)
    arr = None
    if pm:
        found = [int(x, 16) for x in re.findall(r'0x([0-9a-fA-F]+)', pm.group(1))]
        if len(found) == 40:
            arr = found
    if arr is None:
        arr = ACW_ARR
    q = [None] * 40
    for x in range(40):
        for z in range(40):
            if arr[z] == x + 1:
                q[z] = arg1[x]
    if any(v is None for v in q):
        return None
    uq = ''.join(q)
    k = acw_key(html)
    return ''.join('%x' % (int(uq[i], 16) ^ int(k[i], 16)) for i in range(40))


def acw_need(resp):
    try:
        t = resp.text
    except Exception:
        return False
    return ('acw_sc__v2' in t) and ("arg1='" in t) and len(t) < 20000


def acw_handle(req, resp, again):
    if not acw_need(resp):
        return resp
    v = acw_solve(resp.text)
    if not v:
        logger.warning('WAF 挑战识别到但未能解出')
        return resp
    req.cookies.set('acw_sc__v2', v, domain='bbs.binmt.cc', path='/')
    logger.info('WAF 挑战已破解, 重新请求')
    r = again()
    r.encoding = r.apparent_encoding
    return r


def acw_get(req, url, **kw):
    resp = req.get(url, **kw)
    resp.encoding = resp.apparent_encoding
    return acw_handle(req, resp, lambda: req.get(url, **kw))


def acw_post(req, url, **kw):
    resp = req.post(url, **kw)
    resp.encoding = resp.apparent_encoding
    return acw_handle(req, resp, lambda: req.post(url, **kw))


def validate_ip_port(ip, port):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_multicast or ip_obj.is_unspecified:
            return False
    except ValueError:
        return False
    ip_parts = ip.split('.')
    for part in ip_parts:
        if not 0 <= int(part) <= 255:
            return False
    if not 1 <= int(port) <= 65535:
        return False
    return True

def verify(proxy):
    target_url = 'https://bbs.binmt.cc/forum.php?mod=guide&view=hot'
    proxies = {
        'https': f'http://{proxy}',
        'http': f'http://{proxy}'
    }
    start_time = time.time()
    try:
        response = requests.get(target_url, headers=headers, proxies=proxies, timeout=20)
        return proxy, response.ok, int((time.time() - start_time) * 1000)
    except:
        return proxy, False, -1

def is_phone_number(username):
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, username) is not None

def format_phone_number(phone):
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone

def format_username(username):
    if is_phone_number(username):
        return format_phone_number(username)
    return username

def load():
    myset = set()
    successful_proxies = []
    try:
        with open("src/ips.txt", "r", encoding="utf-8") as f:
            for line in f:
                ip = line.strip()
                if ":" not in ip or not ip: continue
                newIp, newPort = ip.split(':', 1)
                if not validate_ip_port(newIp, newPort): continue
                myset.add(ip)
    except Exception as e:
        pass
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(verify, proxy) for proxy in myset]
        for future in as_completed(futures):
            proxy, is_valid, requestTime = future.result()
            if is_valid:
                successful_proxies.append((proxy, requestTime))
    successful_proxies.sort(key=lambda x: x[1])
    logger.info("可用ip代理:")
    for index, (proxy, req_time) in enumerate(successful_proxies, 1):
        logger.info(f"{index}: {proxy} - {req_time}ms")
        IP_LIST[proxy] = True

def checkIn(user, pwd, ip=None):
    global hasE
    req = requests.session()
    req.headers.update(headers)
    if ip:
        proxies = {
            'http': f'http://{ip}',
            'https': f'http://{ip}'
        }
        req.proxies = proxies
    else:
        proxies = None
    logger.info(f"{format_username(user)} 开始签到")
    try:
        url = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
        resp = acw_get(req, url, proxies=proxies, timeout=20)
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
            resp = acw_post(req, url, data=data, proxies=proxies, timeout=20)
            resp.encoding = resp.apparent_encoding
            if resp.ok:
                if '失败' in resp.text:
                    del accounts_list[user]
                    logger.warning(f"{user}: 密码错误")
                    hasE = True
                    RESULT_PWDERR.append(user)
                    return
                url = 'https://bbs.binmt.cc/k_misign-sign.html'
                resp = acw_get(req, url, proxies=proxies, timeout=20)
                resp.encoding = resp.apparent_encoding
                _formhash = formhash(resp.text)
                code = resp.status_code
                if resp.ok:
                    url = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={_formhash}'
                    resp = acw_get(req, url, proxies=proxies, timeout=20)
                    resp.encoding = resp.apparent_encoding
                    if '已签' in resp.text:
                        del accounts_list[user]
                        logger.info(CDATA(resp.text))
                        prefs.put(user, prefs.getTime())
                        return True
                    _msg = CDATA(resp.text)
                    logger.warning(_msg if _msg else '签到失败, 响应片段: ' + resp.text[:120].replace('\n', ' '))
    except Exception as e:
        logger.warning(f"异常: {str(e)}")
        if ip:
            IP_LIST[ip] = False
    return False

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

def send_serverchan(title, desp):
    if not SENDKEY:
        logger.info('未配置 SENDKEY, 跳过 Server酱推送')
        return
    try:
        r = requests.post(f'https://sctapi.ftqq.com/{SENDKEY}.send',
                          data={'title': title, 'desp': desp}, timeout=15)
        j = r.json()
        if j.get('code') == 0:
            logger.info('Server酱推送成功')
        else:
            logger.warning(f'Server酱推送失败: {j}')
    except Exception as e:
        logger.warning(f'Server酱推送异常: {e}')

def push_report():
    if not (RESULT_OK or RESULT_SKIP or RESULT_FAIL or RESULT_PWDERR):
        return
    if hasE or RESULT_FAIL or RESULT_PWDERR:
        title = f"❌ MT签到异常 成功{len(RESULT_OK)} 失败{len(RESULT_FAIL) + len(RESULT_PWDERR)}"
    else:
        title = f"✅ MT签到成功 共{len(RESULT_OK) + len(RESULT_SKIP)}个账户"
    sections = []
    for label, lst in (('签到成功', RESULT_OK), ('今日已签', RESULT_SKIP),
                       ('签到失败', RESULT_FAIL), ('密码错误', RESULT_PWDERR)):
        if lst:
            names = ', '.join(format_username(u) for u in lst)
            sections.append(f"- **{label}**({len(lst)}): {names}")
    desp = f"**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n" + "\n".join(sections)
    send_serverchan(title, desp)

def start():
    ACCOUNTS = os.environ.get("ACCOUNTS", "")
    if not ACCOUNTS:
        logger.warning('github ACCOUNTS变量未设置')
        exit(1)
    for duo in ACCOUNTS.split("\n"):
        if ':' not in duo:
            continue
        username, password = duo.split(':', 1)
        username = username.strip()
        password = password.strip()
        YiQianDao = prefs.get(username, "") == prefs.getTime()
        if username and password and not YiQianDao:
            accounts_list[username] = password
        elif YiQianDao:
            RESULT_SKIP.append(username)
            logger.info(f"{format_username(username)} 今日已签, 跳过签到")
    if accounts_list:
        load()
    global sign_fail
    keys = list(accounts_list.keys())
    total = len(keys)
    if total:
        targets = [p for p, s in IP_LIST.items() if s]
        targets.append(None)
        for i, username in enumerate(keys):
            ok = False
            for proxy in targets:
                try:
                    if checkIn(username, accounts_list[username], proxy):
                        ok = True
                        break
                except:
                    pass
            if ok:
                RESULT_OK.append(username)
                logger.info(f"{format_username(username)} 签到成功")
            else:
                sign_fail += 1
                RESULT_FAIL.append(username)
                logger.warning(f"{format_username(username)} 今日签到失败")
            if i < total - 1:
                time.sleep(3)
start()
prefs.save()
push_report()
if hasE or sign_fail: exit(1)