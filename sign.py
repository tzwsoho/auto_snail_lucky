import time
import frida
import base64
import _thread

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

def alipay_sign(s, operation_type, request_data, ts):
    t = {
        'operationType': operation_type,
        'requestData': request_data,
        'ts': ts
    }
    return s.exports.sign_request(t)

def on_ready(s):
    while 1:
        print('*' * 150)
        print('直接按下 CTRL+C 退出程序')
        operation_type = input('请输入 Operation-Type：')
        request_data = base64.b64encode(bytearray(input('请输入 Request-Data：'), 'utf-8')).decode('utf-8')
        ts = input('请输入 Ts（留空则取当前时间）：')
        if ts == '':
            ts = get_ts()
        print('待签名串：Operation-Type=' + operation_type + '&Request-Data=' + request_data + '&Ts=' + ts)
        print('签名是：', alipay_sign(s, operation_type, request_data, ts))

max_instances = 12
def on_message(message, payload):
    # print(message)
    # print(payload.decode('utf-8'))
    if message['type'] != 'send':
        return

    if (message['payload'] == max_instances):
        _thread.start_new_thread(on_ready, (script,))

script.on('message', on_message)
script.load()
print('请随意点击几羊界面以产生 HTTP 请求，本代码需要收集签名函数动态地址...')

# input() # 等待输入
while 1:
    time.sleep(1)

session.detach()
