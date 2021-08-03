import time
import frida
import zlib

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
with open('../index.js') as f:
    script = session.create_script(f.read())

def on_message(message, payload):
    # print(message)
    # print(payload.decode('utf-8'))

    if message['payload'] == 100 or message['payload'] == 101: # SSL_read/SSL_write
        pl = payload.split(b'\r\n\r\n', 1)
        if len(pl) == 2:
            headers = ''
            try:
                headers = pl[0].decode('utf-8')
            except:
                print(pl[0])
            post_data = pl[1]
            if headers.find('Content-Encoding: gzip') >= 0:
                if message['payload'] == 100: # SSL_read
                    post_data = pl[1].split(b'\r\n', 1)
                    if len(post_data) == 2:
                        try:
                            post_data = zlib.decompress(post_data[1], 16 + zlib.MAX_WBITS)
                        except:
                            print(post_data[1])
                        else:
                            post_data = ''
                elif message['payload'] == 101: # SSL_write
                    try:
                        post_data = zlib.decompress(post_data, 16 + zlib.MAX_WBITS)
                    except:
                        print(post_data)
                    else:
                        post_data = ''
            try:
                post_data = post_data.decode('utf-8')
            except:
                print(post_data)
            else:
                post_data = ''
            print('SSL_read' if message['payload'] == 100 else 'SSL_write', '\n' + headers, '\n\n' + post_data, '\n', '*' * 120)

script.on('message', on_message)
script.load()
print('请随意点击几羊界面以产生 HTTP 请求...')

input() # 按下 Enter 退出
# while 1:
    # time.sleep(1)

session.detach()
