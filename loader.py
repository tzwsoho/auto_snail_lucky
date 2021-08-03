import json
import time
import frida
import base64
import _thread
import urllib.request

device = frida.get_usb_device()
pid = 0

for snail_lucky in device.enumerate_processes():
    if snail_lucky.name.find('几羊') >= 0:
        pid = snail_lucky.pid
        break

if pid == 0:
    pid = device.spawn('com.snail.android.lucky')
    device.resume(pid)

if pid == 0:
    os._exit(0)

print(pid)

session = device.attach(pid)
with open('index.js') as f:
    script = session.create_script(f.read())

instances = set()
a = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd',
    'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
    'y', 'z', '+', '/'
]

def c10to64(j):
    p = 2 ** 6
    cArr = bytearray(p)
    i = p
    while 1:
        i -= 1
        cArr[i] = ord(a[63 & j])
        j = j >> 6
        if j == 0:
            break
    return cArr.decode('utf-8').strip('\0')

def get_ts():
    tm = int(time.time() * 1000)
    return c10to64(tm)

# print(get_ts())

def alipay_sign(s, operation_type, request_data, ts):
    t = {
        'operationType': operation_type,
        'requestData': base64.b64encode(bytearray(request_data, 'utf-8')).decode('utf-8'),
        'ts': ts
    }
    # print(str(t))
    return s.exports.sign_request(t)

def alipay_headers(s, base_info, operation_type, ts, sign):
    android_id = s.exports.get_check_android_id()
    channel_id = s.exports.get_channel_id()
    imei = s.exports.get_imei()
    mac = s.exports.get_mac()
    workspace_id = s.exports.get_workspace_id()
    app_id = s.exports.get_app_id()
    version = s.exports.get_version()
    product_id = s.exports.get_app_key_from_meta_data()
    did = s.exports.get_device_id()
    cookie = s.exports.get_cookie()
    return {
        'platform': base_info['platform'],
        'androidid': android_id,
        'channelid': channel_id,
        'imei': imei,
        'token': base_info['token'],
        'userid': base_info['userId'],
        'clientversion': base_info['clientVersion'],
        'mac': mac,
        'clientkey': base_info['clientKey'],
        'utdid': base_info['utdid'],
        'apdid': base_info['apdid'],
        'model': base_info['model'],
        'WorkspaceId': workspace_id,
        'AppId': app_id,
        'Platform': 'ANDROID',
        'productVersion': version,
        'productId': product_id,
        'Version': '2',
        'Did': did,
        'Operation-Type': operation_type,
        'Ts': ts,
        'Content-Type': 'application/json',
        'Sign': sign,
        'signType': '0',
        'Cookie': cookie,
        'Accept-Language': 'zh-Hans',
        'Connection': 'Keep-Alive',
        'Retryable2': '0',
        'Host': 'snailgw.shulidata.com',
        'User-Agent': 'Android_Ant_Client'
    }

def build_curl(headers, data):
    s = 'curl'
    for k, v in headers.items():
        s += ' -H \'' + str(k) + ': ' + str(v) + '\''
    s += ' --data \'' + str(data) + '\' \'https://snailgw.shulidata.com/mgw.htm\''
    print(s)

def alipay_request(headers, data):
    url = 'https://snailgw.shulidata.com/mgw.htm'
    build_curl(headers, data)

    req = urllib.request.Request(url, bytearray(data, 'utf-8'), headers)
    res = urllib.request.urlopen(req).read()
    print(res.decode('utf-8'))

def alipay_mobile_aggrbillinfo_drm_client_info(s):
    operation_type = 'alipay.mobile.aggrbillinfo.drm.client.info'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([ base_info ], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    alipay_request(headers, request_data);

def alipay_mobile_aggrbillinfo_quota_userinfo(s):
    operation_type = 'alipay.mobile.aggrbillinfo.quota.userinfo'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([ base_info ], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    alipay_request(headers, request_data);

def on_ready(s):
    # print('get_cookie = ' + s.exports.get_cookie())
    # print('get_rpc_base_info = ' + s.exports.get_rpc_base_info())
    # print('get_device_id = ' + s.exports.get_device_id())
    # print('get_app_id = ' + s.exports.get_app_id())
    # print('get_app_key_from_meta_data = ' + s.exports.get_app_key_from_meta_data())
    # print('get_version = ' + s.exports.get_version())
    # print('get_imei = ' + s.exports.get_imei())
    # print('get_check_android_id = ' + s.exports.get_check_android_id())
    # print('get_channel_id = ' + s.exports.get_channel_id())
    # print('get_mac = ' + s.exports.get_mac())
    # print('get_workspace_id = ' + s.exports.get_workspace_id())
    # alipay_mobile_aggrbillinfo_drm_client_info(s)
    alipay_mobile_aggrbillinfo_quota_userinfo(s)

max_instances = 12
def on_message(message, payload):
    # print(message)
    # print(payload.decode('utf-8'))
    if message['type'] != 'send':
        return

    if ((message['payload'] >= 1) or (message['payload'] <= max_instances)):
        instances.add(message['payload'])
        print('Got ' + str(len(instances)) + '/' + str(max_instances) + ': ' + str(instances))
        if len(instances) == max_instances:
            print('Got All!')
            _thread.start_new_thread(on_ready, (script,))

script.on('message', on_message)
script.load()
print('请点击几羊收取羊毛的界面，本代码共需要收集 ' + str(max_instances) + ' 个函数或类实例的相关信息...')

input() # 等待输入

session.detach()
