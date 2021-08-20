#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import json
import time
import frida
import gzip
import base64
import random
import _thread
import requests
import traceback
import functools
import webbrowser
import urllib.parse

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#################################################################################################################################################

app_version = '3.1.0' # 每次有版本更新时需要用 ssl_tool 重新获取
client_version = '3.6.1.0' # 每次有版本更新时需要用 ssl_tool 重新获取
request_interval = 0.1 # 每个请求的间隔时间，不要弄太快小心被封

#################################################################################################################################################

device = frida.get_usb_device()
pid = 0

# for snail_lucky in device.enumerate_processes():
    # if snail_lucky.name.find('几羊') >= 0:
        # pid = snail_lucky.pid
        # break

# if pid == 0:
    # pid = device.spawn('com.snail.android.lucky')
    # device.resume(pid)

app = device.get_frontmost_application()
if app is not None:
    pid = app.pid

# app = device.get_frontmost_application()
# if app is not None:
    # pid = app.pid

if pid == 0:
    os._exit(0)

print('几羊进程 ID：', pid)

session = device.attach(pid)
with open('index.js') as f:
    script = session.create_script(f.read())

#################################################################################################################################################

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
    c_arr = bytearray(p)
    i = p
    while 1:
        i -= 1
        c_arr[i] = ord(a[63 & j])
        j = j >> 6
        if j == 0:
            break
    return c_arr.decode('utf-8').strip('\0')

def get_ts():
    tm = int(time.time() * 1000)
    return c10to64(tm)

# print(get_ts())

#################################################################################################################################################

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
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive',
        'Retryable2': '0',
        'Content-Encoding': 'gzip',
        'Host': 'snailgw.shulidata.com',
        'User-Agent': 'Android_Ant_Client'
    }

def build_curl(headers, data):
    s = 'curl'
    for k, v in headers.items():
        if k.find('Content-Encoding') >= 0 or k.find('Accept-Encoding') >= 0:
            continue

        s += ' -H \'' + str(k) + ': ' + str(v) + '\''

    s += ' --data \'' + str(data) + '\' \'https://snailgw.shulidata.com/mgw.htm\''
    print('*' * 120, '\n', s, '\n' + '*' * 120)

def alipay_request(headers, data):
    url = 'https://snailgw.shulidata.com/mgw.htm'
    # build_curl(headers, data)
    ret = ''

    try:
        data = gzip.compress(data.encode('utf-8'))
        res = requests.post(url, headers = headers, data = data, verify = False, timeout = 20)

        # 每个请求间隔一段时间，避免封号
        if request_interval > 0:
            time.sleep(request_interval)

        ret = res.content.decode('utf-8')
        # print('*' * 120, '\n', ret, '\n' + '*' * 120)
        return json.loads(ret)
    except Exception:
        traceback.print_exc()
        print('!' * 120, '\n', ret, '\n' + '!' * 120)
        return dict()

#################################################################################################################################################

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","model":"NX563J","platform":"Android","systemSwitchStatus":true,"token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取用户每日签到信息
# {"giftHighestInfo":"本周连开7天得钻石宝箱","giftTodayInfo":"今日签到奖励：铂金宝箱","idem":true,"lastWeekDay":"2021.08.08","levelChange":"0","levelChangeDocument":"成功保级新贵铂金","levelName":" 新贵铂金","memberLevel":"3","myRedPoint":true,"propsGiftBox":{"bizType":"SIGN_IN","divination":{"bizType":"UP_UP","guaCi":"柔顺谦虚","level":"上上卦","name":"升卦","revelation1":"尽情感受今天的美好","revelation2":"今日幸运数字：3","yaoCi":"六四：王用亨于岐山。吉，无咎。"},"expireTime":1628092800000,"giftBoxId":"2021080403185252070","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hEECTZv48ecAAAAAAAAAAAAAARQnAQ","level":"3","status":"WAIT_OPEN","tip":"点击可开宝箱哦～","title":"铂金宝箱","type":"PLATINUM"},"signIconList":["https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*6OfuSbxT6gYAAAAAAAAAAAAAARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*6OfuSbxT6gYAAAAAAAAAAAAAARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*3lZiQaY01DAAAAAAAAAAAAAAARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*jSJcTrl8zQUAAAAAAAAAAAAAARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*jSJcTrl8zQUAAAAAAAAAAAAAARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*jSJcTrl8zQUAAAAAAAAAAAAAARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*-BMVT7vLBY8AAAAAAAAAAAAAARQnAQ"],"signRuleUrl":"https://render.alipay.com/p/c/181mt9ik8zxc","success":true,"switchStatus":"OFF","todaySignInGiftLevel":"3","totalQuota":"35000.00","totalSignNum":3,"userType":"OLD_MEMBER"}
def alipay_mobile_aggrbillinfo_user_sign(s):
    operation_type = 'alipay.mobile.aggrbillinfo.user.sign'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'platform': base_info['platform'],
        'systemSwitchStatus': True,
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"s4qNdokoIt","clientVersion":"3.4.0.69","model":"NX563J","platform":"Android","token":"a1a78e5f20ddbe470e108e7f253ef9fd","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取用户限额信息
# {"availableQuota":"35000.00","goldNum":20,"goldNumStr":"20","idem":false,"limitQuota":"6500","success":true,"totalQuota":"35000.00","totalWool":"14000.00","userShowInfoVo":{"avatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","cancelRelationFlag":false,"endColor":"#D8B09A","genderLabel":"M","growthScore":"288","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"","memberLevel":"3","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nextLevelDocument":"还需1306成长值下周可升级史诗钻石会员","nextLevelGrowthScore":"1594","nickName":"tzw_work","officialLabel":"NORMAL","otherLabel":[],"startColor":"#F9E3D6","userId":"8088025113224702"},"woolFull":false,"woolSpeed":"1.4"}
def alipay_mobile_aggrbillinfo_quota_userinfo(s):
    operation_type = 'alipay.mobile.aggrbillinfo.quota.userinfo'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","idfa":"","platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取背包里面的卡片列表
# {"idem":false,"propVoList":[{"color":"#FF8025","desc":"小羊产毛速度+0.4/s","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*k5fQTYQFLOsAAAAAAAAAAAAAARQnAQ","quantity":1,"status":"UN_USED","title":"产毛加速卡","type":"SHEEP_SPEED_2"},{"color":"#FF4C25","desc":"活动参与次数+1","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*bcwzTZ51r20AAAAAAAAAAAAAARQnAQ","quantity":45,"status":"UN_USED","title":"活动次数卡","type":"LOTTERY_VICE_ACTIVITY_1"},{"color":"#FFBB00","desc":"羊毛+1500","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*lE-jQYl4YHYAAAAAAAAAAAAAARQnAQ","quantity":3,"status":"UN_USED","title":"羊毛卡","type":"SHEEP_WOOL_2"}],"success":true}
def alipay_mobile_aggrbillinfo_sheep_prop_list(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.prop.list'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","cardId":"","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","consumeNum":1,"idfa":"","platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","type":"SHEEP_WOOL_2","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 使用背包里面的卡片
# {"errorCode":"90005","errorMsg":"可用羊毛已满，先去抽个奖再来使用吧～","idem":false,"success":false}
def alipay_mobile_aggrbillinfo_props_card_use(s, consume_num, card_type):
    operation_type = 'alipay.mobile.aggrbillinfo.props.card.use'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'cardId': '',
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'consumeNum': consume_num,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'type': card_type,
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","idfa":"","platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取收羊毛界面信息
# {"availableBottle":0,"availableFodder":332,"availableQuota":"35000.00","availableWool":"14000.00","avatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","dynamicUrl":"alipays://platformapi/startapp?appId=2021001152630129&query=publicId%3D2021001107603955","goldNum":20,"hasGold":false,"hasGoldToast":"主人，我挖到了很多金币，有空可以去收取哦～","idem":true,"limitQuota":"6500","limitQuotaBonus":"","limitQuotaBonusExpireSeconds":0,"lookUrl":"alipays://platformapi/startapp?appId=2019112669453030","moodUrl":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*U0QTQLKnTXMAAAAAAAAAAAAAARQnAQ","needFeedTimes":50,"needReceiveSheep":false,"newActivityType":"newcomerTask","nickName":"tzw_work","raiderUrl":"https://render.alipay.com/p/c/1816wmrzl5og","ruleUrl":"https://render.alipay.com/p/c/1816pcztl4n4","sheepMood":"100","sheepStatus":"IDLE","sheepWorkToast":"小羊外出打工赚金币啦\n点我立即召回小羊","success":true,"totalBottle":0,"totalQuota":"25000.00","totalQuotaBonus":"","totalQuotaBonusExpireSeconds":0,"totalWool":"14000.00","totalWoolBonus":"","totalWoolBonusExpireSeconds":0,"userShowInfoVo":{"avatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","cancelRelationFlag":false,"endColor":"#D8B09A","genderLabel":"M","growthScore":"288","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"","memberLevel":"3","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nextLevelDocument":"还需1306成长值下周可升级史诗钻石会员","nextLevelGrowthScore":"1594","nickName":"tzw_work","officialLabel":"NORMAL","otherLabel":[],"startColor":"#F9E3D6","userId":"8088025113224702"},"userType":"OLD_USER","woolSpeed":1.4,"woolSpeedBonus":"","woolSpeedBonusExpireSeconds":0,"workEndSeconds":0,"workUrl":"alipays://platformapi/startapp?appId=2019112669453030"}
def alipay_mobile_aggrbillinfo_sheep_info(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.info'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"Zp2SAUBucQ","clientVersion":"3.2.1.0","idfa":"","platform":"h5","token":"6de0d5333632596ec9c067df2c5627f8","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取收羊毛界面额外信息
# {"acquireFodderTimeStr":"","acquireFodderToast":"点我领8g饲料","availableBottle":20,"hasAcquireFodder":true,"idem":true,"moodPrompt":"OFF","needFeedTimes":49,"rapidFeedingVo":{"bizType":"RAPID_FEEDING","status":"ON"},"sheepTalkVo":{"actionTxt":"","prompt":"羊毛满了，快点击收取吧","switchStatus":true,"title":"快来收羊毛","type":"none","url":""},"success":true,"totalBottle":1000}
def alipay_mobile_aggrbillinfo_sheep_info_extra(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.info.extra'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.5.1.0","idfa":"","platform":"h5","token":"19a5d2f04e7cb5579df1302682d3747a","userId":"8088027101103706","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 收集羊奶
# {"availableBottle":0,"goldNum":20,"idem":false,"needFeedTimes":50,"success":true,"totalBottle":1000}
def alipay_mobile_aggrbillinfo_sheep_collect_milk(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.collectMilk'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.5.1.0","idfa":"","platform":"h5","token":"1a8cfba775c8d44db131d9bbc133c9cb","userId":"8088015060932312","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取羊奶兑换现金的商品列表
# {"activityInfos":[{"activityType":"RANDOM","goldNum":0,"goldStr":"对应100-100000羊奶","iconBackGroupColor":"#FD6561","iconText":"随机提现","money":0,"moneyStr":"0.01-10.00元","priority":1,"showAppWithDrawBtnTxt":false},{"activityType":"WITHDRAW_1000","goldNum":99950,"goldStr":"对应99,950羊奶","iconBackGroupColor":"#FD6561","iconText":"超高人气","money":1000,"moneyStr":"10.00元","priority":2,"showAppWithDrawBtnTxt":false},{"activityType":"WITHDRAW_2000","goldNum":199800,"goldStr":"对应199,800羊奶","iconBackGroupColor":"#FD6561","iconText":"超高人气","money":2000,"moneyStr":"20.00元","priority":3,"showAppWithDrawBtnTxt":false},{"activityType":"WITHDRAW_5000","goldNum":499000,"goldStr":"对应499,000羊奶","iconBackGroupColor":"#BFBFBF","iconText":"秒到账","money":5000,"moneyStr":"50.00元","priority":5,"showAppWithDrawBtnTxt":false},{"activityType":"WITHDRAW_10000","goldNum":998000,"goldStr":"对应998,000羊奶","iconBackGroupColor":"#BFBFBF","iconText":"最划算","money":10000,"moneyStr":"100.00元","priority":6,"showAppWithDrawBtnTxt":false},{"activityType":"WITHDRAW_20000","goldNum":1994000,"goldStr":"对应1994,000羊奶","iconBackGroupColor":"#BFBFBF","iconText":"最划算","money":20000,"moneyStr":"200.00元","priority":7,"showAppWithDrawBtnTxt":false}],"alertText":"xxxxx","appWithDrawBtnTxt":"APP专享","bindAlipayStatus":true,"bindWeixinpayStatus":false,"goldNumStr":"93,920","goldToMoneyStr":"9.39","idem":false,"noBindText":"暂未绑定支付宝账号","sheepMood":"100","sheepMoodCopywriting":"小羊心情值100，心情不错，羊奶很新鲜","sheepMoodPopupsCopywriting":"当心情值<10时，将每天扣减500羊奶；\n经常来看看，每天能提升3心情值，让羊奶不过期","success":true,"typeInfoList":[{"icon":"xxx","name":"支付宝","type":"ALI_PAY"}]}
def alipay_mobile_aggrbillinfo_withdraw_index(s):
    operation_type = 'alipay.mobile.aggrbillinfo.withdraw.index'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"activityType":"RANDOM","appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.5.1.0","idfa":"","platform":"h5","token":"1a8cfba775c8d44db131d9bbc133c9cb","userId":"8088015060932312","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx","withdrawType":"ALI_PAY"}]
# 兑换羊奶为现金
# {"errorCode":"0099","errorMsg":"今日随机提现次数用完咯，明日再来试试","idem":false,"success":false}
# {"errInfoList":[{"clickButtonText":"支付宝","clickUrl":"xxx","title":"金额少于最小金额"}],"idem":false,"spendGoldNumStr":"200","status":"SUCC","statusIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*yArvTo0MkTMAAAAAAAAAAAAAARQnAQ","statusText":"提现成功","succButtonText":"去支付宝查看","success":true,"topIcon":"","topText":"金额将提现至您当前账户绑定的支付宝账户上，请注意查收 。","transId":"2021081402203138531","transferTimeStr":"2021-08-14 01:35:23","withdrawMoneyStr":"￥0.02"}
def alipay_mobile_aggrbillinfo_withdraw_withdraw(s, activity_type):
    operation_type = 'alipay.mobile.aggrbillinfo.withdraw.withdraw'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityType': activity_type,
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
        'withdrawType': 'ALI_PAY',
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.5.1.0","idfa":"","platform":"h5","token":"1a8cfba775c8d44db131d9bbc133c9cb","transId":"2021081402203138531","userId":"8088015060932312","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取兑换羊奶结果
# {"errInfoList":[{"clickButtonText":"支付宝","clickUrl":"xxx","title":"金额少于最小金额"}],"idem":false,"spendGoldNumStr":"200","status":"SUCC","statusIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*yArvTo0MkTMAAAAAAAAAAAAAARQnAQ","statusText":"提现成功","succButtonText":"去支付宝查看","success":true,"topIcon":"","topText":"金额将提现至您当前账户绑定的支付宝账户上，请注意查收 。","transId":"2021081402203138531","transferTimeStr":"2021-08-14 01:35:23","withdrawMoneyStr":"￥0.02"}
def alipay_mobile_aggrbillinfo_withdraw_result(s, trans_id):
    operation_type = 'alipay.mobile.aggrbillinfo.withdraw.result'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'transId': trans_id,
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.5.1.0","idfa":"","platform":"h5","token":"19a5d2f04e7cb5579df1302682d3747a","userId":"8088027101103706","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 收取羊毛
# {"availableBottle":0,"availableFodder":0,"availableQuota":"20000.00","availableWool":"9890.00","goldNum":0,"hasGold":false,"hasGoldToast":"","idem":true,"limitQuota":"5500","limitQuotaBonus":"","limitQuotaBonusExpireSeconds":0,"needFeedTimes":50,"needReceiveSheep":true,"sheepStatus":"IDLE","sheepTalkVo":{"actionTxt":"去抽奖","extInfo":"{\"appId\":\"60000001\"}","prompt":"羊毛已充足，快去抽 奖吧","switchStatus":true,"title":"羊毛充足快抽奖吧","type":"native","url":""},"sheepWorkToast":"","success":true,"totalBottle":0,"totalQuota":"20000.00","totalQuotaBonus":"","totalQuotaBonusExpireSeconds":0,"totalWool":"12000.00","totalWoolBonus":"","totalWoolBonusExpireSeconds":0,"woolSpeed":1.2,"woolSpeedBonus":"","woolSpeedBonusExpireSeconds":0,"workEndSeconds":0}
def alipay_mobile_aggrbillinfo_sheep_wool_collect(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.wool.collect'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.5.1.0","idfa":"","platform":"h5","token":"19a5d2f04e7cb5579df1302682d3747a","userId":"8088027101103706","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 领取饲料弹窗
# {"buttonStr":"去领取","canAcquireFodder":"80","fodderNumStr":"","idem":true,"linkUrl":"wisheep://platformapi/startApp?appId=60000004&activityId=2021080500821414400","needLotteryCountStr":"","status":"CAN_ACQUIRE","success":true}
def alipay_mobile_aggrbillinfo_sheep_fodder_popup(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.fodder.popup'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"s4qNdokoIt","clientVersion":"3.4.1.0","idfa":"","platform":"h5","token":"a1a78e5f20ddbe470e108e7f253ef9fd","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取收羊毛界面领饲料任务列表
# {"hasAcquireFodder":true,"icon":"","idem":false,"success":true,"taskList":[{"buttonText":"打卡","clickUrl":"","currentNum":0,"remainTime":0,"sortNum":1,"taskIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*BAXxT4OH7WAAAAAAAAAAAAAAARQnAQ","taskId":100001,"taskJumpType":"CLICK","taskPrizeNum":100,"taskPrizeType":"FODDER","taskStatus":"INIT","taskSubTitle":"每日可以打卡2次 ，每次领100g饲料","taskTitle":"每日打卡领饲料","taskType":"FUNCTION","timeLimit":10,"totalNum":2},{"buttonText":"去看看","clickUrl":"","currentNum":0,"extInfo":"{\"iosCodeId\":\"945970401\",\"androidCodeId\":\"945990692\"}","remainTime":0,"sortNum":2,"taskIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*9RZkQLt0L0gAAAAAAAAAAAAAARQnAQ","taskId":100007,"taskJumpType":"JUMP_AD","taskPrizeNum":500,"taskPrizeType":"FODDER","taskStatus":"INIT","taskSubTitle":"每日可以看3次视频，每次领500g饲料","taskTitle":"每日看视频","taskType":"POWER","timeLimit":10,"totalNum":3},...],"taskTabVo":{"angleTitle":"抽奖领饲料","fodderNumStr":"80","leftButtonText":"去查看","needLotteryCountStr":"6","rightButtonText":"去抽奖","status":"NORMAL","title":"16"},"title":"领饲料"}
def alipay_mobile_aggrbillinfo_sheep_tasklist(s):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.tasklist'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"s4qNdokoIt","clientVersion":"3.4.1.0","idfa":"","platform":"h5","taskId":100008,"token":"a1a78e5f20ddbe470e108e7f253ef9fd","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 完成收羊毛界面任务
# {"idem":false,"remainTime":0,"success":true,"taskPrizeNum":1000,"taskPrizeType":"FODDER","taskStatus":"FINISHED"}
def alipay_mobile_aggrbillinfo_sheep_finishtask(s, task_id):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.finishtask'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'taskId': task_id,
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"s4qNdokoIt","clientVersion":"3.4.1.0","idfa":"","platform":"h5","taskId":100001,"taskPrizeNum":100,"token":"a1a78e5f20ddbe470e108e7f253ef9fd","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 领取收羊毛界面任务奖励
# {"idem":false,"remainTime":0,"success":true}
def alipay_mobile_aggrbillinfo_sheep_taskaward(s, task_id, task_prize_num):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.taskaward'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'platform': 'h5',
        'taskId': task_id,
        'taskPrizeNum': task_prize_num,
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"s4qNdokoIt","clientVersion":"3.4.1.0","fodderNum":1000,"idfa":"","platform":"h5","token":"a1a78e5f20ddbe470e108e7f253ef9fd","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 喂羊
# 饲料只能为 100 或者 1000
# {"availableBottle":240,"availableFodder":432,"idem":false,"needFeedTimes":38,"success":true,"totalBottle":1000}
def alipay_mobile_aggrbillinfo_sheep_feed(s, fodder_num):
    operation_type = 'alipay.mobile.aggrbillinfo.sheep.feed'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'fodderNum': fodder_num,
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","gitBoxId":"2021080403186251470","idfa":"","platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 开宝箱领取卡片
# {"idem":false,"recommendCards":[{"cardDesc":"羊毛+2000","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*P3MtQZmSnFwAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"3","quantity":1,"status":"UN_USED","title":"羊毛卡","type":"SHEEP_WOOL_3","value":"2000.0","win":false},{"cardDesc":"可抽商品上限+2000元","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*obj3SKojXcEAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"3","quantity":1,"status":"UN_USED","title":"抽奖升值卡","type":"ITEM_PRICE_3","value":"2000.0","win":false},{"cardDesc":"可抽商品上限+2500元","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*En4ERqDhBp4AAAAAAAAAAAAAARQnAQ","extDesc":"","level":"4","quantity":1,"status":"UN_USED","title":"抽奖升值卡","type":"ITEM_PRICE_4","value":"2500.0","win":false},{"cardDesc":"小羊产毛速度+0.4/s","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*k5fQTYQFLOsAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"2","quantity":1,"status":"UN_USED","title":"产毛加速卡","type":"SHEEP_SPEED_2","value":"0.4","win":false},{"cardDesc":"活动参与次数+1","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*bcwzTZ51r20AAAAAAAAAAAAAARQnAQ","cardId":"2021080403118957670","extDesc":"","level":"1","quantity":1,"status":"UN_USED","title":"活动次数卡","type":"LOTTERY_VICE_ACTIVITY_1","value":"1.0","win":true},{"cardDesc":"羊毛+10000","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hA5oSq73i_cAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"4","quantity":1,"status":"UN_USED","title":"羊毛卡","type":"SHEEP_WOOL_4","value":"10000.0","win":false},{"cardDesc":"羊奶+1000","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hBGCSq3V-tcAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"3","quantity":1,"status":"UN_USED","title":"羊奶卡","type":"PRIZE_3","value":"1000.0","win":false},{"cardDesc":"小羊产毛速度+0.6/s","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*qgAbQpW2wKIAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"3","quantity":1,"status":"UN_USED","title":"产毛加速卡","type":"SHEEP_SPEED_3","value":"0.6","win":false},{"cardDesc":"小羊容量+10000","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*PMmmQ60rzpwAAAAAAAAAAAAAARQnAQ","extDesc":"","level":"4","quantity":1,"status":"UN_USED","title":"小羊容量卡","type":"SHEEP_QUOTA_4","value":"10000.0","win":false}],"success":true}
def alipay_mobile_aggrbillinfo_props_gift_box_open(s, box_id):
    operation_type = 'alipay.mobile.aggrbillinfo.props.gift.box.open'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'gitBoxId': box_id, # 几羊作者的拼写错误，应为 giftBoxId
        'idfa': '',
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","model":"NX563J","platform":"Android","token":"","userId":"","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取抽奖大厅分类列表
# {"availableQuota":"20000.00","cateConfs":[{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"6708\"}","title":"推荐"}],"title":"推荐"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3756\"}","title":"百货"}],"title":"百货"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3761\"}","title":"美食"}],"title":"美食"},{"indexTabConfVos":[{"paramStr":"{\"queryWord\": \"手机\"}","title":"手机"}],"title":"手机"},{"indexTabConfVos":[{"paramStr":"{\"queryWord\": \"电脑\"}","title":"电脑"}],"title":"电脑"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3759\"}","title":"家电"}],"title":"家电"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3767\"}","title":"美衣"}],"title":"美衣"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3764\"}","title":"男装"}],"title":"男装"},{"indexTabConfVos":[{"paramStr":"{\"queryWord\": \"饰品\"}","title":"饰品"}],"title":"饰品"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3763\"}","title":"美妆"}],"title":"美妆"},{"indexTabConfVos":[{"paramStr":"{\"queryWord\": \"家纺\"}","title":"家纺"}],"title":"家纺"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3758\"}","title":"家居"}],"title":"家居"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3766\"}","title":"运动"}],"title":"运动"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3760\"}","title":"母婴"}],"title":"母婴"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3765\"}","title":"内衣"}],"title":"内衣"},{"indexTabConfVos":[{"paramStr":"{\"materialId\": \"3762\"}","title":"鞋包"}],"title":"鞋包"},{"indexTabConfVos":[{"paramStr":"{\"queryWord\": \"车饰\"}","title":"车品"}],"title":"车品"}],"categories":[{"materialId":"6708","name":"推荐"},{"favoritesId":"2020738001","materialId":"31539","name":"豪礼"},{"materialId":"3756","name":"热门"},{"materialId":"3761","name":"美食"},{"materialId":"3763","name":"美妆"},{"materialId":"3759","name":"家电"},{"materialId":"3767","name":"美衣"},{"materialId":"3760","name":"母婴"},{"materialId":"3758","name":"家居"},{"materialId":"3762","name":"鞋包"},{"materialId":"3765","name":"内衣"},{"materialId":"3764","name":"男装"},{"materialId":"3766","name":"运动"}],"continueSignNum":"0","duplicateActivityVos":[],"everyLoginQuota":false,"idem":true,"itemVoList":[{"activityId":"2021080500821414400","afterButtonText":"已参与","basePrice":0,"beforeButtonText":"免费抽奖","expireFlag":false,"itemId":"624225931498","itemNum":0,"itemType":"TBK_GOODS","lotteryPersonText":"累计70.12万人参与抽奖","luckDogText":"已有1人中奖","needPropNum":0,"participateCount":701169,"pictUrl":"https://img.alicdn.com/i3/654143820/O1CN01QMTSrq1e5bfK...
def alipay_mobile_aggrbillinfo_user_sign_list(s):
    operation_type = 'alipay.mobile.aggrbillinfo.user.sign.list'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)
    # cateConfs 字段下为各分类信息

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","model":"NX563J","pageNo":2,"pageSize":20,"paramStr":"{\"materialId\": \"6708\"}","platform":"Android","remainTime":72,"token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取抽奖大厅列表
# {"duplicateActivityVos":[{"activityIcon1":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*W9nXSZAfv1QAAAAAAAAAAAAAARQnAQ","activityIcon2":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*bsxbSrx-xmgAAAAAAAAAAAAAARQnAQ","activityName":"千人团进行中","activityStatus":"INIT","activityStatusText":"进行中","activityType":"THOUSAND","backGroupImg":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hzL8RJ-NeSAAAAAAAAAAAAAAARQnAQ","context":"千人组团","currentLocation":true,"dateStr":"今日","endTime":1628071200000,"itemInfoList":[{"groupNum":1300,"pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg"},{"groupNum":1300,"pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01aomRpl2JEDM10QjYz_!!2200778929389-0-cib.jpg_350x350.jpg"},{"groupNum":1200,"pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01eMsyp41L4iBv2okr4_!!2410081246-0-cib.jpg_350x350.jpg"}],"openTime":1628078400000,"priority":1,"prizeText":"已有197787人中奖","ruleUrl":"https://render.alipay.com/p/c/18357y4lalr4","startTime":1628053200000,"timeStr":"13:00"}],"idem":false,"itemVoList":[{"activityId":"2021080400816262800","afterButtonText":"已参与","basePrice":0,"beforeButtonText":"免费抽奖","expireFlag":false,"itemId":"536454755630","itemNum":0,"itemType":"TBK_GOODS","lotteryPersonText":"累计608人参与抽奖","needPropNum":0,"participateCount":608,"pictUrl":"https://img.alicdn.com/bao/uploaded/i3/1611893164/O1CN01ClgGJ01ZF9l974Cqu_!!0-item_pic.jpg_350x350.jpg","price":0,"salePrice":"79.00","status":"INIT","title":"㊙赤豪澳洲家庭儿童牛排套餐10刀叉","tmallBrandName":"赤豪食品","volume":22,"whiteImage":"https://img.alicdn.com/bao/uploaded/TB1Av3WOsfpK1RjSZFOSuu6nFXa.jpg_350x350.jpg"},{"activityId":"2021080400816262800","afterButtonText":"已参与","basePrice":0,"beforeButtonText":"免费抽奖","expireFlag":false,"itemId":"545009700223","itemNum":0,"itemType":"TBK_GOODS","lotteryPersonText":"累计1085人参与抽奖","needPropNum":0,"participateCount":1085,"pictUrl":"https://img.alicdn.com/bao/uploaded/i2/2780830659/O1CN01EGNvay1GjrgeICkdR_!!2780830659.jpg_350x350.jpg","price":0,"salePrice":"16.80","status":"INIT","title":"男士秋裤单...
# param_str 对应 alipay_mobile_aggrbillinfo_user_sign_list 函数返回 cateConfs 字段下 indexTabConfVos 字段下的 paramStr
def alipay_mobile_aggrbillinfo_mall_list(s, page_no, page_size, param_str, remain_time):
    operation_type = 'alipay.mobile.aggrbillinfo.mall.list'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'pageNo': page_no,
        'pageSize': page_size,
        'paramStr': param_str,
        'platform': base_info['platform'],
        'remainTime': remain_time,
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"activityId":"2021080400816262800","apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","itemId":"527565445184","lotteryType":"MANUAL","model":"NX563J","platform":"Android","token":"46d492d238ce6908915c0f797437bb0d","type":"TBK_GOODS","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 抽奖大厅抽奖
# {"idem":false,"lotteryCode":"3097296","lotteryRecordId":"2021080404219067270","lotteryStatus":"GOING_LOTTERY","success":true}
def alipay_mobile_aggrbillinfo_lottery_lottery(s, activity_id, item_id, lottery_type, good_type):
    operation_type = 'alipay.mobile.aggrbillinfo.lottery.lottery'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityId': activity_id,
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'itemId': item_id,
        'lotteryType': lottery_type,
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'type': good_type,
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","lotteryId":"2021080404219067270","model":"NX563J","platform":"Android","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 抽奖大厅抽奖后的摇一摇
# lottery_id 为 alipay_mobile_aggrbillinfo_lottery_lottery 结果里面的 lotteryRecordId
# {"groupQuota":"0.00","groupRecords":[{"activityId":"2021080400816262800","avatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","genderLabel":"M","groupRecordId":"2021080404007137870","itemClickUrl":"tbopen://m.taobao.com/tbopen/index.html?action=ali.open.nav&module=h5&source=alimama&bc_fl_src=tunion_vipmedia_sy&h5Url=https%3A%2F%2Fuland.taobao.com%2Fcoupon%2Fedetail%3Fe%3DySOLPQDP7GsNfLV8niU3RxrSI%252FOabn6qNg4Gqf8CT4BnmB%252Fzds2ljTK0xeURgcat6mvTIANPDPY6SO0CnGpJKpU2YvrCJCERCARcrbx6Zw%252BZC%252FtTa4oRES2rYrCt7FoTFKiJWcE6lIHrIYDh7lBWFtyCJA2ajj11yvtiGWy5Te8V%252FVWXG0UTeMjqsMFcqaMK09n1P0j5XaIJP8D1%252BglCLSUzVkkdwsIm%26%26app_pvid%3D59590_33.5.137.212_804_1628067859452%26ptl%3DfloorId%3A2836%3Bapp_pvid%3A59590_33.5.137.212_804_1628067859452%3Btpp_pvid%3A100_11.12.65.5_2390_1861628067859457077%26xId%3DTVWwsT9SmElOomJTP0bwqhb6T3wK7tDjnCAzivKdcoNHsbna3sSNav8z03Kpb83ngLkOv5mjsvEfG49HRTo31eX4ujuLqmJQVlanmhX3cpP%26union_lens%3DlensId%253AMAPI%25401628067859%2540210589d4_088c_17b10680c0c_8e26%254001%26relationId%3D2590722717","itemId":"527565445184","lotteryCode":"3097296","lotteryRecordId":"2021080404219067270","nickName":"tzw_work","otherLabel":[],"pictUrl":"https://img.alicdn.com/bao/uploaded/i2/2362736194/O1CN01EhMuu01vctuz08tEv_!!0-item_pic.jpg","prizeType":"GROUP","salePrice":"18.80","status":"GOING","title":"名师手把手小学生日记周记小学书籍","userId":"8088025113224702","userShowInfoVo":{"avatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","cancelRelationFlag":false,"endColor":"#D8B09A","genderLabel":"M","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nickName":"tzw_work","officialLabel":"NORMAL","otherLabel":[],"startColor":"#F9E3D6","userId":"8088025113224702"},"whiteImgUrl":"https://img.alicdn.com/bao/uploaded/TB1RXk8X4jaK1RjSZFASuvdLFXa.jpg"}],"groupStatus":"GOING_GROUPED","idem":false,"success":true}
def alipay_mobile_aggrbillinfo_group_yaoyiyao(s, lottery_id):
    operation_type = 'alipay.mobile.aggrbillinfo.group.yaoyiyao'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'lotteryId': lottery_id,
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"activityType":"THOUSAND","appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","idfa":"","pageNo":1,"pageSize":100,"platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 组团抽奖活动信息列表
# activity_type 有三种：HUNDREDS - 百人团，THOUSAND - 千人团，TEN_THOUSAND - 万人团
# {"duplicateActivityVos":[{"activityName":"千人团进行中","activityStatus":"INIT","activityStatusText":"进行中","activityType":"THOUSAND","backGroupImg":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hzL8RJ-NeSAAAAAAAAAAAAAAARQnAQ","currentLocation":true,"dateStr":"今日","endTime":1628071200000,"openTime":1628078400000,"priority":1,"prizeText":"","ruleUrl":"https://render.alipay.com/p/c/18357y4lalr4","startTime":1628053200000,"timeStr":"13:00"},{"activityName":"万人团即将开始","activityStatus":"WAIT_START","activityStatusText":"即将开始","activityType":"TEN_THOUSAND","backGroupImg":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*ftv-SrN3OeQAAAAAAAAAAAAAARQnAQ","currentLocation":false,"dateStr":"今日","endTime":1628092800000,"openTime":1628121600000,"priority":2,"prizeText":"","ruleUrl":"https://render.alipay.com/p/c/1835a10an7cw","startTime":1628071200000,"timeStr":"18:00"},{"activityName":"百人团即将开始","activityStatus":"WAIT_START","activityStatusText":"即将开始","activityType":"HUNDREDS","backGroupImg":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*D-G9RaToQ_EAAAAAAAAAAAAAARQnAQ","currentLocation":false,"dateStr":"明日","endTime":1628139600000,"openTime":1628146800000,"priority":3,"prizeText":"","ruleUrl":"https://render.alipay.com/p/c/18357y4lalr4","startTime":1628092800000,"timeStr":"00:00"}],"idem":false,"indexItemVoList":[{"activityId":"2021080400815764900","basePrice":0,"expireFlag":false,"itemId":"cyb2021073000004132100","itemNum":2000,"itemNumStr":"x2000","itemType":"ONE_SEE_GOODS","needPropNum":1,"pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01WPzzUI1V0GVKWmkBu_!!2211032012590-0-cib.jpg_350x350.jpg","price":0,"salePrice":"6.51","title":"抖音同款保湿防晒喷雾150ml","usePropNum":"x1","whiteImage":"https://cbu01.alicdn.com/img/ibank/O1CN01WPzzUI1V0GVKWmkBu_!!2211032012590-0-cib.jpg_350x350.jpg"},{"activityId":"2021080400815764900","basePrice":0,"expireFlag":false,"itemId":"cyb2021060800003597700","itemNum":1300,"itemNumStr":"x1300","itemType":"ONE_SEE_GOODS","luckDogText":"已有5401人中奖","needPropNum":1,"pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01fXBiSQ1dhn2AaVbLx_!!2207073863768-0-cib.jpg_350x350.jpg","price":0,"salePrice":"9.89","title":"巧克力脆筒零食238g/盒","usePropNum":"x1","whiteImage":"https://cbu01.alicdn.com/img/ibank/O1CN01fXBiSQ1dhn2AaVbLx_!!2207073863768-0-cib.jpg_350x350.jpg"},{"activityId":"2021080400815764900","basePrice":0,"expireFlag":false,"itemId":"cyb2021072000003838400","itemNum":1300,"itemNumStr":"x1300","itemType":"ONE_SEE_GOODS","needPropNum":1,"pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01aomRpl2JEDM10QjYz_!!2200778929389-0-cib.jpg_350x350.jpg","price":0,"salePrice":"9.37","title":"超值口腔清洁十二件套","usePropNum":"x1","whiteImage":"https://cbu01.alicdn.com/img/ibank/O1CN01aomRpl2JEDM10QjYz_!!2200778929389-0-cib.jpg_350x350.jpg"}....,"propsCardVo":{"cardDesc":"活动参与次数+1","cardIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*bcwzTZ51r20AAAAAAAAAAAAAARQnAQ","extDesc":"app用户加成","level":"1","quantity":5,"status":"UN_USED","title":"活动次数卡","type":"LOTTERY_VICE_ACTIVITY_1","value":"1.0","win":true},"success":true,"userPropNum":50}
def alipay_mobile_aggrbillinfo_duplicate_tab(s, activity_type, page_no, page_size):
    operation_type = 'alipay.mobile.aggrbillinfo.duplicate.tab'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityType': activity_type,
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'pageNo': page_no,
        'pageSize': page_size,
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)
    # duplicateActivityVos 为活动列表，activityStatus 为 INIT 的活动为正在进行的活动，activityType 为活动类型
    # userPropNum 为剩余抽奖次数
    # indexItemVoList 为抽奖信息列表

# [{"activityId":"2021080400815764900","activityType":"THOUSAND","appName":"","appVersion":"3.1.0","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","idfa":"","itemId":"cyb2021031800002214200","itemType":"ONE_SEE_GOODS","platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 组团抽奖活动状态及剩余抽奖次数
# {"idem":false,"lotteryStatus":"FINISHED","success":true,"userPropNum":49}
def alipay_mobile_aggrbillinfo_duplicate_lottery_status(s, activity_id, activity_type, item_id, item_type):
    operation_type = 'alipay.mobile.aggrbillinfo.duplicate.lottery.status'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityId': activity_id,
        'activityType': activity_type,
        'appName': '',
        'appVersion': app_version,
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'itemId': item_id,
        'itemType': item_type,
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"activityId":"2021080400815764900","activityType":"THOUSAND","apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","itemId":"cyb2021031800002214200","itemType":"ONE_SEE_GOODS","model":"NX563J","platform":"Android","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 组团抽奖活动抽奖
# 抽奖信息在 alipay_mobile_aggrbillinfo_duplicate_tab 函数返回的 indexItemVoList 字段下面：
'''
{
	"indexItemVoList": [
		{
			"activityId": "2021080400815764900",
			"basePrice": 0,
			"expireFlag": false,
			"itemId": "cyb2021031800002214200",
			"itemNum": 1300,
			"itemNumStr": "x1300",
			"itemType": "ONE_SEE_GOODS",
			"luckDogText": "已有11700人中奖",
			"needPropNum": 1,
			"pictUrl": "https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg",
			"price": 0,
			"salePrice": "9.63",
			"title": "几羊定制好运便携餐盒",
			"usePropNum": "x1",
			"verifyIndexPictUrl": "https://mdn.alipayobjects.com/portal_o2iec2/afts/img/A*BTktQI4Whj8AAAAAAAAAAAAAAQAAAQ/original_350x350.jpg",
			"verifyTitle": "几羊定制好运便携餐盒",
			"whiteImage": "https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg"
		},
        ...
'''
# {"idem":false,"lotteryCode":"3954209","lotteryRecordId":"2021080404226142070","lotteryStatus":"GROUP_UP_ING","success":true}
def alipay_mobile_aggrbillinfo_duplicate_lottery(s, activity_id, activity_type, item_id, item_type):
    operation_type = 'alipay.mobile.aggrbillinfo.duplicate.lottery'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityId': activity_id,
        'activityType': activity_type,
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'itemId': item_id,
        'itemType': item_type,
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"activityId":"2021080400815764900","apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","lotteryRecordId":"2021080404226142070","model":"NX563J","platform":"Android","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 组团抽奖活动抽奖后的摇一摇
# lottery_record_id 为 alipay_mobile_aggrbillinfo_duplicate_lottery 函数返回的 lotteryRecordId
# {"groupId":"2021080400106686946","idem":false,"luckyStatus":"GOING","memberTotal":979,"memberVoList":[{"activityId":"2021080400815764900","extInfo":{"itemType":"ONE_SEE_GOODS","itemVolume":"null","itemTitle":"几羊定制好运便携餐盒","city":"Guangzhou","userAvatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","activityEnv":"PROD","activityId":"2021080400815764900","needPropNum":"1","memberPrivacy":"OFF","avatarEndColor":"#D8B09A","province":"Guangdong","itemCentPrice":"963","activityOpenTime":"2021-08-04 20:00:00","userNickName":"tzw_work","avatarStartColor":"#F9E3D6","memberLevel":"3","activityName":"20210804期-千人团","itemWhiteImage":"https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg","processItemId":"cyb2021031800002214200","userId":"8088025113224702","itemPictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg","cybBasePrice":"740","itemId":"cyb2021031800002214200","userUserName":"18529787350","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","itemSalePrice":"9.63","itemSource":"淘宝","userGender":"男","activityType":"THOUSAND","activityPeriod":"2021-08-04"},"gmtCreate":1628069638000,"gmtGroup":1628069638000,"gmtModified":1628069638000,"groupId":"2021080400106686946","itemId":"cyb2021031800002214200","itemPrice":963,"itemVo":{"centPrice":"963","discount":"0","expireFlag":false,"itemId":"cyb2021031800002214200","itemSource":"淘宝","itemType":"ONE_SEE_GOODS","pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg","salePrice":"9.63","title":"几羊定制好运便携餐盒","whiteImage":"https://cbu01.alicdn.com/img/ibank/O1CN01neVnhF1ri9zEKXR75_!!2208161825664-0-cib.jpg_350x350.jpg"},"lotteryCode":"3954209","lotteryRecordId":"2021080404226142070","memberId":"2021080400250847246","partTimeStr":"刚刚参与抽奖","status":"SUCCESS","type":"THOUSAND","userId":"8088025113224702","userShowInfoVo":{"avatar":"https://thirdwx.qlogo.cn/mmopen/vi_32/P20nZfsvjEIXSiaciacKbVu4I4GvicK0aWHI8Er1AzBIlj5bUY3krEO8Ia3FeKazLa5eVW00BOyQGnX2rZjvabn5Q/132","cancelRelationFlag":false,"endColor":"#D8B09A","genderLabel":"M","growthScore":"288","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"","memberLevel":"3","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nextLevelDocument":"还需1306成长值下周可升级史诗钻石会员","nextLevelGrowthScore":"1594","nickName":"tzw_work","officialLabel":"NORMAL","otherLabel":[],"startColor":"#F9E3D6","userId":"8088025113224702"}},{"activityId":"2021080400815764900","extInfo":{"itemType":"ONE_SEE_GOODS","itemVolume":"null","itemTitle":"几羊定制好运便携餐..."lotteryCode":"1575147","lotteryRecordId":"2021080404151011381","memberId":"2021080400201566246","partTimeStr":"5分钟前参与抽奖","status":"SUCCESS","type":"THOUSAND","userId":"8088000067824819","userShowInfoVo":{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*KlAeSpE9loAAAAAAAAAAAAAADsZ1AA/original?t=QMA1g2EjtN3OJIjVtTgY8QAAAABkdcYAAAAA","cancelRelationFlag":false,"endColor":"#D8B09A","genderLabel":"","growthScore":"626","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*K7ksSbuhBnEAAAAAAAAAAAAAARQnAQ","memberLevel":"3","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nextLevelDocument":"还需968成长值下周可升级史诗钻石会员","nextLevelGrowthScore":"1594","nickName":"高大的树木","officialLabel":"NORMAL","otherLabel":[],"startColor":"#F9E3D6","userId":"8088000067824819"}}],"success":true}
def alipay_mobile_aggrbillinfo_duplicate_group_yaoyiyao(s, activity_id, lottery_record_id):
    operation_type = 'alipay.mobile.aggrbillinfo.duplicate.group.yaoyiyao'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityId': activity_id,
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'lotteryRecordId': lottery_record_id,
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","lotteryRecordId":"2021080404229474031","model":"NX563J","platform":"Android","token":"11c5e7c791bf727e5d43c1c3f5b0a308","userId":"8088015060932312","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 领取组团抽奖活动奖励
# {"cashPrizeAlertVo":{"backGroupImg":"","doublePrice":"0.42","finalButtonText":"去查看","finalTitle":"已领取到我的羊奶,可提现哦","originPrice":"0.00","timeButtonText":"会员特权，羊奶限时翻倍","timeTitleText":"立即翻倍","timesStr":"已翻1.3倍"},"idem":false,"redBagType":"WAN_REN_PARTITION","success":true}
def alipay_mobile_aggrbillinfo_duplicate_award(s, lottery_record_id):
    operation_type = 'alipay.mobile.aggrbillinfo.duplicate.award'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'lotteryRecordId': lottery_record_id,
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

# [{"apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","bizScene":"HOT","bizSource":"INDEX_TAB","clientKey":"IBdxM1u3SL","clientVersion":"3.5.0.73","model":"NX563J","pageNo":2,"pageSize":20,"platform":"Android","remainTime":23,"token":"1a8cfba775c8d44db131d9bbc133c9cb","topLuckyRecordId":"","userId":"8088015060932312","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取发现频道晒奖列表
# {"idem":false,"propsGiftBox":{"bizType":"SHARE_SQUARE","expireTime":1628870400000,"giftBoxId":"2021081303346819431","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*kvxBT7RkWcEAAAAAAAAAAAAAARQnAQ","level":"2","status":"WAIT_OPEN","tip":"点击可开宝箱哦～","title":"黄金宝箱","type":"GOLD"},"recommendShareInfo":{"itemType":"ONE_SEE_GOODS","lotteryRecordId":"2021080204178453831","pictUrl":"https://cbu01.alicdn.com/img/ibank/O1CN01lf1qUF1ri9zRPSZny_!!2208161825664-0-cib.jpg_350x350.jpg","recommendShare":true},"shareLatestTime":1628838734314,"shareRecords":[{"activityId":"2021072100703711800","activityType":"SINGLE_LOTTERY","auditReason":"","auditStatus":"PASS","avatar":"https://tfs.alipayobjects.com/images/partner/TB1pzC0bzyEDuNkUQusXXbvMVXa","city":"昆明","commentInfo":{"commentCount":2240,"latestComments":[{"birthLabel":"95后","city":"深圳","comment":"羡慕","commentIcon":"","commentId":"2021081301095554656","commentTemplateId":"1bc2b87b376d01bf8024c987f8a5909a","commentTime":"3小时前","commentTransId":"2021081302548408610","status":"PUBLISH","thumbUpTotal":0,"userAvatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*Hrp0RK4W78YAAAAAAAAAAAAADsZ1AA/original?t=y5evWEjglK3rokuwnGhjIwAAAABkdcYAAAAA","userGender":"M","userId":"8088017131220566","userNickName":"海龟","userShowInfoVo":{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*Hrp0RK4W78YAAAAAAAAAAAAADsZ1AA/original?t=y5evWEjglK3rokuwnGhjIwAAAABkdcYAAAAA","cancelRelationFlag":false,"constellationLabel":"双鱼座","endColor":"#D8B09A","genderLabel":"M","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*K7ksSbuhBnEAAAAAAAAAAAAAARQnAQ","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nickName":"海龟","officialLabel":"NORMAL","otherLabel":["95后","深圳"],"startColor":"#F9E3D6","userId":"8088017131220566"},"userTag":""},{"birthLabel":"05后","city":"桂林","comment":"轻轻一点，运气加倍，嘿嘿","commentIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*ZbngSoXNdfMAAAAAAAAAAAAAARQnAQ","commentId":"2021081301131699248","commentTemplateId":"39","commentTime":"7小时前","commentTransId":"2021081302539867910","status":"PUBLISH","thumbUpTotal":0,"userAvatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*xJvlRaUvrMUAAAAAAAAAAAAADsZ1AA/original?t=bcfTRKLEst_7KX9YsSuOiAAAAABkdcYAAAAA","userGender":"F","userId":"8088004036374489","userNickName":"爱笑的女孩运气不差吧","userShowInfoVo":{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*xJvlRaUvrMUAAAAAAAAAAAAADsZ1AA/original?t=bcfTRKLEst_7KX9YsSuOiAAAAABkdcYAAAAA","cancelRelationFlag":false,"constellationLabel":"双鱼座","endColor":"#D8B09A","genderLabel":"F","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*K7ksSbuhBnEAAAAAAAAAAAAAARQnAQ","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nickName":"爱笑的女孩运气不差吧","officialLabel":"NORMAL","otherLabel":["05后","桂林"],"startColor":"#F9E3D6","userId":"8088004036374489"},"userTag":""}]},"gender":"M","gmtOpen":1626919200000,"imageUrls":["https://mdn.alipayobjects.com/snail_avatar/afts/img/A*8HaQSpWjBaAAAAAAAAAAAAAAAQAAAQ/80p","https://mdn.alipayobjects.com/snail_avatar/afts/img/A*gKRxToKdcCcAAAAAAAAAAAAAAQAAAQ/80p"],"item":{"discount":"169.98","expireFlag":false,"finalPrice":"9829.02","itemClickUrl":"tbopen://m.taobao.com/tbopen/index.html?action=ali.open.nav&module=h5&source=alimama&bc_fl_src=tunion_vipmedia_sy&h5Url=https%3A%2F%2Fs.click.taobao.com%2Ft%3Fe%3Dm%253D2%2526s%253DthjpdjGz7rtw4vFB6t2Z2ueEDrYVVa64r4ll3HtqqoxyINtkUhsv0Dx1W73Y%252BDaE%252Fc5HvFSRlDF8wNSpnfMOYxuOf%252Fc28c7F9HCa%252BmBT5tVCP5SCFWxeqrutGDFC4Ggc1GPduzu4oNoy8vgdE4C5iTQMk5v3Gg14PTEHn5TWCEb16UiVr4iIsd9AyuQiphV2xgxdTc00KD8%253D%26scm%3Dnull%26pvid%3D100_11.178.152.80_120842_7011626849622871936%26app_pvid%3D59590_33.4.180.204_751_1626849622866%26ptl%3DfloorId%3A2836%3BoriginalFloorId%3A2836%3Bpvid%3A100_11.178.152.80_120842_7011626849622871936%3Bapp_pvid%3A59590_33.4.180.204_751_1626849622866%26xId%3D1831AoUlWSe5UIGO8dyuXKNxvS9O1d1aSPsEBFTmmcCTIUHv54ES3cYbRf6eD99CB8VZnxCU8xs7oa9X893quFJzz0EjPMAZbXOPXeFGaZ8R%26union_lens%3DlensId%253AMAPI%25401626849622%25402104b4cc_0857_17ac7cb3b64_2c9f%254001%26relationId%3D2590722717","itemId":"627941215987","itemSource":"淘宝","itemType":"TBK_GOODS","pictUrl":"https://img.alicdn.com/bao/uploaded/i3/3221418665/O1CN01gcvVcI2Dscb32THfM_!!0-item_pic.jpg","salePrice":"9999.00","title":"samsung /三星qa55q700tajxxz电视","whiteImage":""},"lastAuditedTime":1627626326000,"lastSubmitTime":1627547761000,"lotteryCode":"7231004","lotteryCodeSource":"CUSTOMIZE","lotteryRecordId":"2021072103887790413","luckyType":"PERSON","nickName":"好","period":"2021-07-21","recordLabel":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*VJUrQ6AzKSMAAAAAAAAAAAAAARQnAQ","secStatus":"UN_CHECK","shareContent":"天天忙着抽大奖，几羊好运送到家。自从玩几羊以来，只要有空就抽奖，自选码出了后，终于自选码立功了。希望几羊越做越好，财源滚滚！也祝玩 几羊的朋友们运气爆棚，也让我再沾沾光。","shareRecordId":"2021072202166121000","shareTime":1627626326000,"shareVideoInfoList":[],"status":"AUDIT_PASS","subTitle":"20210721期中奖","tag":"70后","thumbUpInfo":{"canPickLuck":false,"thumbUpCount":1237,"thumbed":false},"type":"OFFICIAL","userId":"8088000569523132","userShowInfoVo":{"avatar":"https://tfs.alipayobjects.com/images/partner/TB1pzC0bzyEDuNkUQusXXbvMVXa","cancelRelationFlag":false,"constellationLabel":"处女座","endColor":"#737E9A","genderLabel":"M","growthScore":"1671","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*GtpkRqQBOncAAAAAAAAAAAAAARQnAQ","lotteryLabel":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*K7ksSbuhBnEAAAAAAAAAAAAAARQnAQ","memberLevel":"4","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hkKKRpOxZpMAAAAAAAAAAAAAARQnAQ","nextLevelDocument":"还需785成长值下周可升级传承黑金会员","nextLevelGrowthScore":"2456","nickName":"好","officialLabel":"NORMAL","otherLabel":["70后","昆明"],"startColor":"#B0B8D0","userId":"8088000569523132"}},{"activityId":"2021072400726242300","activityType":"SINGLE_LOTTERY","auditReason":"","auditStatus":"PASS","avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*_asPSr2pMWUAAAAAAAAAAAAADsZ1AA/original?t=syIiqHIdWWOWgZjvqxlbDgAAAABkdcYAAAAA","commentInfo":{"commentCount":1236,"latestComments":[{"birthLabel":"10后","city":"广州","comment":"默默赞一下留下羡慕的背影","commentIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*uHZVQb-mGnEAAAAAAAAAAAAAARQnAQ","commentId":"2021081301407490077","commentTemplateId":"17","commentTime":"32分钟前","commentTransId":"2021081302593089466","status":"PUBLISH","thumbUpTotal":0,"userAvatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*6-auSoBHdRYAAAAAAAAAAAAADsZ1AA/original?t=_3UC_Q6mhcdRsKn_2p4GLAAAAABkdcYAAAAA","userGender":"M","userId":"8088012787276778","userNickName":"豁达的八宝粥","userShowInfoVo":{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*6-auSoBHdRYAAAAAAAAAAAAADsZ1AA/original?t=_3UC_Q6mhcdRsKn_2p4GLAAAAABkdcYAAAAA","cancelRelationFlag":false,"constellationLabel":"摩羯 座","endColor":"#D8B09A","genderLabel":"M","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*K7ksSbuhBnEAAAAAAAAAAAAAARQnAQ","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nickName":"豁达的八宝 粥","officialLabel":"NORMAL","otherLabel":["10后","广州"],"startColor":"#F9E3D6","userId":"8088012787276778"},"userTag":""},{"comment":"👍","commentIcon":"","commentId":"2021081300977896445","commentTemplateId":"c0eb33f9757e9085882a3b90a5f73c7b","commentTime":"1小时前","commentTransId":"2021081302592603266","status":"PUBLISH","thumbUpTotal":0,"userAvatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*AYA9S5b8D2cAAAAAAAAAAAAADsZ1AA/original?t=5990jijYjZx5u-czcjp8KQAAAABkdcYAAAAA","userGender":"","userId":"8088017449994452","userNickName":"AI 时代","userShowInfoVo":{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*AYA9S5b8D2cAAAAAAAAAAAAADsZ1AA/original?t=5990jijYjZx5u-czcjp8KQAAAABkdcYAAAAA","cancelRelationFlag":false,"endColor":"#D8B09A","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*bLAXRozD7mUAAAAAAAAAAAAAARQnAQ","lotteryLabel":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*K7ksSbuhBnEAAAAAAAAAAAAAARQnAQ","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*w8ycQpdQKVAAAAAAAAAAAAAAARQnAQ","nickName":"AI 时代","officialLabel":"NORMAL","startColor":"#F9E3D6","userId":"8088017449994452"},"userTag":""}]},"gmtOpen":1627178400000,"imageUrls":["https://mdn.alipayobjects.com/snail_avatar/afts/img/A*BdQ0SKWUrlMAAAAAAAAAAAAAAQAAAQ/80p","https://mdn.alipayobjects.com/snail_avatar/afts/img/A*4y3iTbllB3sAAAAAAAAAAAAAAQAAAQ/80p","https://mdn.alipayobjects.com/snail_avatar/afts/img/A*73sDSJDxwnYAAAAAAAAAAAAAAQAAAQ/80p","https://mdn.alipayobjects.com/snail_avatar/afts/img/A*uI2kTrGTt_AAAAAAAAAAAAAAAQAAAQ/80p","https://mdn.alipayobjects.com/snail_avatar/afts/img/A*yyFnSJFY16MAAAAAAAAAAAAAAQAAAQ/80p"],"item":{"discount":"14.64","expireFlag":false,"finalPrice":"5843.36","itemClickUrl":"tbopen://m.taobao.com/tbopen/index.html?action=ali.open.nav&module=h5&source=alimama&bc_fl_src=tunion_vipmedia_sy&h5Url=https%3A%2F%2Fs.click.taobao.com%2Ft%3Fe%3Dm%253D2%2526s%253DnjbitCLijzZw4vFB6t2Z2ueEDrYVVa64r4ll3HtqqoxyINtkUhsv0N2E%252BqmNVeclIdbSor0PwI18wNSpnfMOYxuOf%252Fc28c7F9HCa%252BmBT5tVCP5SCFWxeqrutGDFC4Ggc1GPduzu4oNoA%252FdY02BsM%252BfIvMmf4HrmBKJGlCwsUoYPNvEJW%252BUp2G99AyuQiphV2xgxdTc00KD8%253D%26scm%3Dnull%26pvid%3D100_11.139.191.152_121246_8531627111927345252%26app_pvid%3D59590_11.186.101.210_799_1627111927340%26ptl%3DfloorId%3A2836%3BoriginalFloorId%3A2836%3Bpvid%3A100_11.139.191.152_121246_8531627111927345252%3Bapp_pvid%3A59590_11.186.101.210_799_1627111927340%26xId%3D6OoOMN88rylYqR2o9py24V5E1YAKWIq4rZLpYDuzXanCiO7VT87E2gDYjoEhuLJFLtVsXHchYx7QmBmsVYWUJzxzjyX2Gv7s7EYvZ6zsLIv2%26union_lens%3DlensId%253AMAPI%25401627111927%25400bba65d2_0e9b_17ad76dae3e_6e70%254001%26relationId%3D2590722717","itemId":"629719200979","itemSource":"淘宝","itemType":"TBK_GOODS","pictUrl":"https://img.alicdn.com/bao/uploaded/i1/2088045547/O1CN01kdx6hf1qqZff1TvxL_!!0-item_pic.jpg","salePrice":"5858.00","title":"优惠750【24期免息】huawei /华为","tmallBrandName":"京合","whiteImage":"https://img.alicdn.com/bao/uploaded/i1/6000000001105/O1CN01l1VlHE1K28IAmuj59_!!6000000001105-0-yinhe.jpg"},"lastAuditedTime":1627626286000,"lastSubmitTime":1627546898000,"lotteryCode":"2699909","lotteryCodeSource":"OWN","lotteryRecordId":"2021072403930830983","luckyType":"PERSON","nickName":"尘土","period":"2021-07-24","recordLabel":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*IXPOQ6YlKwMAAAAAAAAAAAAAARQnAQ","secStatus":"UN_CHECK","shareContent":"我中奖了，努力了大半年，这次7位数全对，1‰万的概率。坎坷和兴奋中等待了三天，现在收到货了，感谢几羊。现在把这份幸运分享给你们，希望...
def alipay_mobile_aggrbillinfo_share_square(s, page_no, page_size, remain_time):
    operation_type = 'alipay.mobile.aggrbillinfo.share.square'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'apdid': base_info['apdid'],
        'bizScene': 'HOT',
        'bizSource': 'INDEX_TAB',
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'pageNo': page_no,
        'pageSize': page_size,
        'platform': base_info['platform'],
        'remainTime': remain_time,
        'token': base_info['token'],
        'topLuckyRecordId': '',
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)


# [{"appName":"","appVersion":"3.1.0","bizType":"LOTTERY","clientKey":"IBdxM1u3SL","clientVersion":"3.4.1.0","idfa":"","pageNo":1,"pageSize":20,"platform":"h5","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 获取消息列表
# {"idem":false,"messageInfos":[{"bizType":"LOTTERY_OPEN","boxIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*wUfHT5SbC7YAAAAAAAAAAAAAARQnAQ","content":"20210803期开奖啦，快看看你是不是幸运儿～","extInfo":"{\"activityId\":\"2021080300805830300\",\"itemId\":\"566542751369\"}","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*joB5Q6oBEn4AAAAAAAAAAAAAARQnAQ","linkUrl":"wisheep://platformapi/startApp?appId=60000004&activityId=2021080300805830300","messageId":"2021080302961158670","nodeType":"MESSAGE","readStatus":"READ","showTime":"10:00","time":1628042404000,"title":"你参与的抽奖开奖啦","unreadCount":0},{"bizType":"LOTTERY_OPEN","boxIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*wUfHT5SbC7YAAAAAAAAAAAAAARQnAQ","content":"20210802期开奖啦，快看看你是不是幸运儿～","extInfo":"{\"activityId\":\"2021080200800227500\",\"itemId\":\"543586438630\"}","icon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*joB5Q6oBEn4AAAAAAAAAAAAAARQnAQ","linkUrl":"wisheep://platformapi/startApp?appId=60000004&activityId=2021080200800227500","messageId":"2021080202929780870","nodeType":"MESSAGE","readStatus":"READ","showTime":"昨天","time":1627956001000,"title":"你参与的抽奖开奖啦","unreadCount":0}...
def alipay_mobile_aggrbillinfo_message_box_list(s, page_no, page_size):
    operation_type = 'alipay.mobile.aggrbillinfo.message.boxList'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'appName': '',
        'appVersion': app_version,
        'bizType': 'LOTTERY',
        'clientKey': base_info['clientKey'],
        'clientVersion': client_version,
        'idfa': '',
        'pageNo': page_no,
        'pageSize': page_size,
        'platform': 'h5',
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)
    # messageInfos 下的 extInfo 字段包含活动 ID

# [{"activityId":"2021080300805830300","apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","model":"NX563J","platform":"Android","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 打开消息获取详情
# {"activityId":"2021081800940906900","activityName":"20210818期-万人团","activityType":"TEN_THOUSAND","discountRecords":[],"failRecordsNew":[{"gmtPart":1629285243000,"groupId":"2021081800114554660","item":{"centPrice":"1000000","discount":"0","expireFlag":false,"itemId":"s0000004","itemSource":"淘宝","itemType":"SPECIFIC_GOODS_2","pictUrl":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*HLHvSImvR48AAAAAAAAAAAAAARQnAQ","salePrice":"10000","subTitle":" 一人中奖，3万人瓜分","title":"100,000,000羊奶","whiteImage":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*HLHvSImvR48AAAAAAAAAAAAAARQnAQ"},"lotteryCode":"7214070","lotteryCodeVoList":[{"content":"1","icon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*-wUKTbPN9tUAAAAAAAAAAAAAARQnAQ","lotteryCode":"7214070","source":"OWN","status":"FAIL","userId":"8088015060932312"}],"numberText":"（第01387团）组团未中奖","recordId":"2021081804595872631","userShowInfoVo":{"avatar":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*_F64TaCS-wgAAAAAAAAAAABkARQnAQ","cancelRelationFlag":false,"nickName":"聪明的灯泡","officialLabel":"NORMAL","userId":"8088015060932312"}},{"gmtPart":1629285232000,"groupId":"2021081800114554760","item":{"centPrice":"1000000","discount":"0","expireFlag":false,"itemId":"s0000003","itemSource":"淘宝","itemType":"SPECIFIC_GOODS_2","pictUrl":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*cyL0T4kWn68AAAAAAAAAAAAAARQnAQ","salePrice":"10000","subTitle":" 一人中奖，2万人瓜分","title":"100,000,000羊奶","whiteImage":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*cyL0T4kWn68AAAAAAAAAAAAAARQnAQ"},"lotteryCode":"9749641","lotteryCodeVoList":[{"content":"1","icon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*-wUKTbPN9tUAAAAAAAAAAAAAARQnAQ","lotteryCode":"9749641","source":"OWN","status":"FAIL","userId":"8088015060932312"}],"numberText":"（第01388团）组团未中奖","recordId":"2021081804586249631","userShowInfoVo":{"avatar":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*_F64TaCS-wgAAAAAAAAAAABkARQnAQ","cancelRelationFlag":false,"nickName":"聪明的灯泡","officialLabel":"NORMAL","userId":"8088015060932312"}}],"hasOwn":true,"idem":false,"lotteryOpenDetailRedEnvelopeVo":{"activityId":"2021081800940906900","activityLabel":"1万人组团抽奖","avatarList":["https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*b3bXSIaX-5EAAAAAAAAAAABkARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*VAB_SYvBl5sAAAAAAAAAAABkARQnAQ","https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*-7ifTZk19W4AAAAAAAAAAABkARQnAQ","http://tfs.alipayobjects.com/images/partner/TB1SUnSanVyDuNk6XeaXXXCWXXa"],"gmtPart":1629283724000,"groupId":"2021081800123930760","groupName":"（第01390团）","itemId":"s0000002","itemType":"SPECIFIC_GOODS_2","lotteryCodeVoList":[{"content":"1","icon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*-wUKTbPN9tUAAAAAAAAAAAAAARQnAQ","lotteryCode":"4407577","source":"OWN","status":"SUCCESS","userId":"8088000095460173"}],"numberText":"9999人组团中奖，瓜分100,000,000羊奶","pictUrl":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*qcs8TrUlJygAAAAAAAAAAAAAARQnAQ","salePrice":"10000","subTitle":" 一人中奖，1万人瓜分","title":"100,000,000羊奶","userVoList":[{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*giR6QpI4NtgAAAAAAAAAAAAADsZ1AA/original?t=rGX_0mHpchkx0u9aY18QaAAAAABkdcYAAAAA","canPickLuck":false,"gmtPart":1629283724000,"lotteryCode":"4407577","lotteryRecordId":"2021081804536336317","luckyType":"PERSON_SIMILAR","nickName":"暗の韋小寶°","pickLucked":false,"userId":"8088000095460173","userShowInfoVo":{"avatar":"https://mdn.alipayobjects.com/snail_avatar/afts/img/A*giR6QpI4NtgAAAAAAAAAAAAADsZ1AA/original?t=rGX_0mHpchkx0u9aY18QaAAAAABkdcYAAAAA","cancelRelationFlag":false,"endColor":"#737E9A","latestMemberLevelIcon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*GtpkRqQBOncAAAAAAAAAAAAAARQnAQ","lotteryLabel":"","memberLevelIcon":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*hkKKRpOxZpMAAAAAAAAAAAAAARQnAQ","nickName":"暗の韋小寶°","officialLabel":"NORMAL","startColor":"#B0B8D0","userId":"8088000095460173"}}]},"luckTotalPerson":"10000","luckyCodeGenRuleUrl":"https://render.alipay.com/p/c/1835be0tdsu8","luckyDetail":{"luckyCode":"4407811","luckyComputeDetails":[{"city":"北京","done":true,"gmtCompute":1629327984511,"idx":"1.14","idxCode":"4","order":0,"originIdx":"1.14"},{"city":"上海","done":true,"gmtCompute":1629327984511,"idx":"1.14","idxCode":"4","order":1,"originIdx":"1.14"},{"city":"广州","done":true,"gmtCompute":1629327984511,"idx":"1.10","idxCode":"0","order":2,"originIdx":"1.1"},{"city":"杭州","done":true,"gmtCompute":1629327984511,"idx":"1.17","idxCode":"7","order":3,"originIdx":"1.17"},{"city":"武汉","done":true,"gmtCompute":1629327984511,"idx":"1.08","idxCode":"8","order":4,"originIdx":"1.08"},{"city":"成都","done":true,"gmtCompute":1629327984511,"idx":"1.11","idxCode":"1","order":5,"originIdx":"1.11"},{"city":"郑州","done":true,"gmtCompute":1629327984511,"idx":"1.11","idxCode":"1","order":6,"originIdx":"1.11"}]},"noticeContent":"部分区域疫情影响物流停发通知,查看详情>>>","noticeUrl":"https://render.alipay.com/p/c/181sgrrosmn4","openCodeRuleStr":"今日6点各城市拥堵延时指数","openDetailStatus":"END_OPEN","openRuleUrl":"https://render.alipay.com/p/c/1835be0tdsu8","openTime":1629331200000,"success":true,"successRecords":[{"awardExpireTime":1629763200000,"gmtPart":1629285254000,"groupId":"2021081800123930760","item":{"centPrice":"1000000","discount":"0","expireFlag":false,"itemId":"s0000002","itemSource":"淘宝","itemType":"SPECIFIC_GOODS_2","pictUrl":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*qcs8TrUlJygAAAAAAAAAAAAAARQnAQ","salePrice":"10000","subTitle":" 一人中奖，1万人瓜分","title":"100,000,000羊奶","whiteImage":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*qcs8TrUlJygAAAAAAAAAAAAAARQnAQ"},"lotteryCode":"5056011","lotteryCodeVoList":[{"content":"1","icon":"https://gw.alipayobjects.com/mdn/rms_5b9989/afts/img/A*-wUKTbPN9tUAAAAAAAAAAAAAARQnAQ","lotteryCode":"5056011","source":"OWN","status":"SUCCESS","userId":"8088015060932312"}],"numberText":"（第01390团）组团中奖，瓜分100000000羊奶","recordId":"2021081804590126531","status":"SUCCESS","type":"GROUP","userShowInfoVo":{"avatar":"https://gw.alipayobjects.com/mdn/TinyAppInnovation/afts/img/A*_F64TaCS-wgAAAAAAAAAAABkARQnAQ","cancelRelationFlag":false,"nickName":"聪明的灯泡","officialLabel":"NORMAL","userId":"8088015060932312"}}],"systemTime":1629338367134}
def alipay_mobile_aggrbillinfo_lottery_record_open_detail(s, activity_id):
    operation_type = 'alipay.mobile.aggrbillinfo.lottery.record.open.detail'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityId': activity_id,
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)
    # fodderInfo 饲料信息，oldFodderNum 原饲料数量；realFodderNum 翻倍后饲料数量；times 倍数；status 为 AWARDED 则已领取，为 GOING 则可以领取
    # successRecords 非空为中奖，status 为状态，AWARDED 为已领奖；

# [{"activityId":"2021080300805830300","apdid":"eYOIkqXXI47JWb8cn6D0oxaU6hpIwTEZaRVOVsJYT4PVrbuCEep0RQBG","clientKey":"IBdxM1u3SL","clientVersion":"3.4.0.69","model":"NX563J","platform":"Android","token":"46d492d238ce6908915c0f797437bb0d","userId":"8088025113224702","utdid":"UJDJKxiEx1gDAFIUoLkA0uxx"}]
# 领取开奖后的饲料奖励
# {"idem":false,"success":true}
def alipay_mobile_aggrbillinfo_lottery_record_fodder_receive(s, activity_id):
    operation_type = 'alipay.mobile.aggrbillinfo.lottery.record.fodder.receive'
    base_info = json.loads(s.exports.get_rpc_base_info())
    request_data = json.dumps([{
        'activityId': activity_id,
        'apdid': base_info['apdid'],
        'clientKey': base_info['clientKey'],
        'clientVersion': base_info['clientVersion'],
        'model': base_info['model'],
        'platform': base_info['platform'],
        'token': base_info['token'],
        'userId': base_info['userId'],
        'utdid': base_info['utdid'],
    }], separators=(',', ':'))
    ts = get_ts()
    sign = alipay_sign(s, operation_type, request_data, ts)
    # print(sign)

    headers = alipay_headers(s, base_info, operation_type, ts, sign)
    return alipay_request(headers, request_data)

#################################################################################################################################################

def open_box(s, box_id):
    box_ret = alipay_mobile_aggrbillinfo_props_gift_box_open(s, box_id)
    if 'recommendCards' in box_ret:
        for box in box_ret['recommendCards']:
            if 'win' in box and box['win'] == True:
                print('抽得卡片：' + box['cardDesc'])
                break

def prepare_wool(s):
    available_quota = float(0) # 目前可用来抽奖的羊毛数
    limit_quota = float(0) # 可抽奖商品价格上限

    sheep_info = alipay_mobile_aggrbillinfo_sheep_info(s)
    if ('availableQuota' in sheep_info
        and 'totalQuota' in sheep_info
        and 'limitQuota' in sheep_info
        and 'availableWool' in sheep_info):
        available_quota = float(sheep_info['availableQuota'])
        limit_quota = float(sheep_info['limitQuota'])

        total_quota = float(sheep_info['totalQuota'])
        available_wool = float(sheep_info['availableWool'])

        print('当前可用来抽奖的羊毛：', available_quota, '可收取羊毛：', available_wool, '可抽奖商品价格上限：', limit_quota)

        if (available_quota < limit_quota
            and available_wool > 0): # 当前用来抽奖的羊毛比可抽奖商品价格上限少，可以先收取羊毛
            print('开始自动收取', (available_wool if available_wool < total_quota - available_quota else total_quota - available_quota), '羊毛...')
            wool_ret = alipay_mobile_aggrbillinfo_sheep_wool_collect(s)
            if ('success' in wool_ret and wool_ret['success']
                and 'availableQuota' in wool_ret):
                available_quota = float(wool_ret['availableQuota'])
            elif 'errorMsg' in wool_ret:
                print('收取羊毛失败：', wool_ret['errorMsg'])
            else:
                print('收取羊毛失败！')

        if available_quota < total_quota: # 如果当前拥有的羊毛比储存上限少，尝试自动使用羊毛卡
            print('尝试自动使用羊毛卡...')
            prop_ret = alipay_mobile_aggrbillinfo_sheep_prop_list(s)
            if 'propVoList' in prop_ret:
                card_used = False
                for prop in prop_ret['propVoList']:
                    if 'desc' in prop and 'type' in prop:
                        re_ret = re.search('羊毛\\+(\\d+)', prop['desc'])
                        if re_ret is not None:
                            wool = int(re_ret.group(1))
                            if available_quota + wool > total_quota: # 已经达到羊毛最大储存限额
                                continue # 有可能还可以使用较小额的羊毛卡

                            print('使用一张', prop['desc'], '卡片...')
                            use_ret = alipay_mobile_aggrbillinfo_props_card_use(s, 1, prop['type'])
                            if ('success' in use_ret
                                and 'toastTxt' in use_ret
                                and use_ret['success']):
                                print(use_ret['toastTxt'])

                                card_used = True
                                available_quota += wool
                            elif 'errorMsg' in use_ret:
                                print('卡片使用失败：', use_ret['errorMsg'])
                                break
                            else:
                                print('卡片使用失败！')
                                break

                if card_used: # 使用卡片后重新获取绵羊信息
                    return prepare_wool(s)

                print('没有找到羊毛卡...')
    return available_quota, limit_quota

def collect_lottery_items_info(s, cate_confs):
    # 收集分类参数
    titles = list()
    param_strs = list()
    print('开始收集商品分类信息...')
    for cate in cate_confs:
        if 'indexTabConfVos' in cate:
            for tab in cate['indexTabConfVos']:
                if 'title' in tab and 'paramStr' in tab:
                    titles.append(tab['title'])
                    param_strs.append(tab['paramStr'])

    # 收集商品信息
    items = dict()
    print('开始收集商品信息...')
    for i in range(0, len(param_strs)):
        page_size = 20 # 每次获取 20 个商品
        max_lottery_pages = 10 # 每个分类获取 10 页数据

        for page in range(1, max_lottery_pages + 1):
            print('正在获取分类', titles[i], '下第', page, '/', max_lottery_pages, '页商品信息，已获取到', len(items), '件商品信息...')

            # TODO 暂时不知道 remainTime 参数的用途，页面定时刷新倒计时？
            # mall_list = alipay_mobile_aggrbillinfo_mall_list(s, page, page_size, param_strs[i], 0)
            mall_list = alipay_mobile_aggrbillinfo_mall_list(s, page, page_size, param_strs[i], random.randint(0, 300))
            if mall_list is None:
                break

            if ('propsGiftBox' in mall_list
                and 'status' in mall_list['propsGiftBox']
                and 'giftBoxId' in mall_list['propsGiftBox']
                and mall_list['propsGiftBox']['status'] == 'WAIT_OPEN'): # 可以开宝箱
                open_box(s, mall_list['propsGiftBox']['giftBoxId'])

            if 'itemVoList' in mall_list:
                for item in mall_list['itemVoList']:
                    if ('title' in item
                        and 'activityId' in item
                        and 'itemId' in item
                        and 'itemType' in item
                        and 'status' in item
                        and 'salePrice' in item
                        and 'participateCount' in item
                        and item['status'] == 'INIT'):
                        sale_price = float(item['salePrice'])
                        items[item['itemId']] = {
                            'title': item['title'],
                            'activityId': item['activityId'],
                            'itemId': item['itemId'],
                            'itemType': item['itemType'],
                            'salePrice': sale_price,
                            'participateCount': item['participateCount']
                        }

    # 对商品排序
    def cmp_item(x, y):
        # 按价格顺序
        if x['salePrice'] < y['salePrice']:
            return -1

        if x['salePrice'] > y['salePrice']:
            return 1

        # 价格一样，按参与人数倒序
        if x['participateCount'] < y['participateCount']:
            return 1

        if x['participateCount'] > y['participateCount']:
            return -1

        return 0

    # 对商品列表排序
    item_list = list()
    for _, v in items.items():
        item_list.append(v)
    item_list.sort(key = functools.cmp_to_key(cmp_item))
    print('已获取到共计', len(item_list), '件商品信息, 现在开始自动抽奖...')

    return item_list

def lottery(s, item, available_quota):
    if (item is None
        or 'title' not in item
        or 'salePrice' not in item
        or 'activityId' not in item
        or 'itemId' not in item
        or 'itemType' not in item):
        return

    print('开始抽奖', '商品为：', item['title'], '价格：', item['salePrice'], '剩余可用羊毛：', available_quota)

    lottery_ret = alipay_mobile_aggrbillinfo_lottery_lottery(s, item['activityId'], item['itemId'], 'MANUAL', item['itemType'])
    if ('success' in lottery_ret
        and lottery_ret['success']
        and 'lotteryRecordId' in lottery_ret): # 继续进行摇一摇
        retries = 0
        yaoyiyao_ret = None
        
        # 按几羊源码，每次间隔时间比上一次多 100ms，一共尝试 7 次
        # com.snail.android.lucky.playbiz.ui.d.c$u -> a -> onResult -> run -> postDelayed
        while (retries < 7
            and (yaoyiyao_ret is None
            or 'groupStatus' not in yaoyiyao_ret
            or 'success' not in yaoyiyao_ret
            or not yaoyiyao_ret['success']
            or yaoyiyao_ret['groupStatus'] != 'GOING_GROUPED')):
            yaoyiyao_ret = alipay_mobile_aggrbillinfo_group_yaoyiyao(s, lottery_ret['lotteryRecordId'])
            time.sleep(0.1 * retries)
            retries += 1

        if (yaoyiyao_ret['success']
            and 'groupRecords' in yaoyiyao_ret
            and len(yaoyiyao_ret['groupRecords']) == 2
            and 'lotteryCode' in yaoyiyao_ret['groupRecords'][0]
            and 'lotteryCode' in yaoyiyao_ret['groupRecords'][1]):
            print('已参加商品', item['title'], '的抽奖',
                '抽奖幸运号码：', yaoyiyao_ret['groupRecords'][0]['lotteryCode'],
                '摇一摇幸运号码：', yaoyiyao_ret['groupRecords'][1]['lotteryCode'])
        elif 'errorMsg' in yaoyiyao_ret:
            print('参与商品', item['title'], '的摇一摇失败：', yaoyiyao_ret['errorMsg'])
        else:
            print('参与商品', item['title'], '的摇一摇失败！')
    elif 'errorMsg' in lottery_ret:
        print('参与商品', item['title'], '的抽奖失败：', lottery_ret['errorMsg'])
    else:
        print('参与商品', item['title'], '的抽奖失败！')

    # 刷新羊毛信息
    limit_quota = float(0)
    sheep_info = alipay_mobile_aggrbillinfo_sheep_info(s)
    if ('availableQuota' in sheep_info
        and 'limitQuota' in sheep_info):
        available_quota = float(sheep_info['availableQuota']) # 目前可用来抽奖的羊毛数
        limit_quota = float(sheep_info['limitQuota']) # 可抽奖商品价格上限

    return available_quota, limit_quota

def on_ready(s):
    while True:
        print('开始获取每日签到信息...')

        sign_info = alipay_mobile_aggrbillinfo_user_sign(s)
        if ('propsGiftBox' in sign_info
            and 'status' in sign_info['propsGiftBox']
            and 'giftBoxId' in sign_info['propsGiftBox']):
            if sign_info['propsGiftBox']['status'] == 'WAIT_OPEN': # 可以开宝箱
                open_box(s, sign_info['propsGiftBox']['giftBoxId'])
            elif sign_info['propsGiftBox']['status'] == 'OPENED': # 宝箱已开
                print('今日签到宝箱已打开！')

        print('已经完成每日签到！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    while True:
        print('开始做领饲料任务...')

        tasklist = alipay_mobile_aggrbillinfo_sheep_tasklist(s)
        if 'taskList' in tasklist:
            for task in tasklist['taskList']:
                if ('remainTime' in task
                    and 'taskId' in task
                    and 'taskJumpType' in task
                    and 'taskStatus' in task
                    and 'taskTitle' in task
                    and 'currentNum' in task
                    and 'totalNum' in task):
                    if (int(task['remainTime']) > 0
                        or task['taskStatus'] == 'FINISHED'
                        or task['currentNum'] == task['totalNum']):
                        continue

                    if task['taskJumpType'].find('JUMP') >= 0:
                        for i in range(0, int(task['totalNum'])):
                            task_ret = alipay_mobile_aggrbillinfo_sheep_finishtask(s, task['taskId'])
                            if ('taskStatus' in task_ret
                                and 'taskPrizeNum' in task_ret
                                and task_ret['taskStatus'] == 'FINISHED'):
                                award_ret = alipay_mobile_aggrbillinfo_sheep_taskaward(s, task['taskId'], task_ret['taskPrizeNum'])
                                if 'success' in award_ret and award_ret['success']:
                                    print('任务 “' + task['taskTitle'] + '” 奖励', task['taskPrizeNum'], '饲料领取成功！')
                                elif 'errorMsg' in award_ret:
                                    print('任务 “' + task['taskTitle'] + '” 奖励领取失败：', award_ret['errorMsg'])
                                else:
                                    print('任务 “' + task['taskTitle'] + '” 奖励领取失败！')

                                print('任务 “' + task['taskTitle'] + '” 成功完成', (i + 1), '/', task['totalNum'], '次！')
                            else:
                                print('任务 “' + task['taskTitle'] + '” 完成失败！')
                                break
                    elif 'taskPrizeNum' in task:
                        award_ret = alipay_mobile_aggrbillinfo_sheep_taskaward(s, task['taskId'], task['taskPrizeNum'])
                        if 'success' in award_ret and award_ret['success']:
                            print('任务 “' + task['taskTitle'] + '” 奖励', task['taskPrizeNum'], '饲料领取成功！')
                        elif 'errorMsg' in award_ret:
                            print('任务 “' + task['taskTitle'] + '” 奖励领取失败：', award_ret['errorMsg'])
                        else:
                            print('任务 “' + task['taskTitle'] + '” 奖励领取失败！')

                        print('任务 “' + task['taskTitle'] + '” 成功完成！')

        print('已经完成领饲料任务！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    while True:
        print('开始喂羊并领羊奶...')

        sheep_info_extra = alipay_mobile_aggrbillinfo_sheep_info_extra(s)
        if ('propsGiftBox' in sheep_info_extra
            and 'giftBoxId' in sheep_info_extra['propsGiftBox']): # 可以开宝箱
            open_box(s, sheep_info_extra['propsGiftBox']['giftBoxId'])

        # 领取饲料
        popup_info = alipay_mobile_aggrbillinfo_sheep_fodder_popup(s)
        if ('status' in popup_info
            and 'linkUrl' in popup_info
            and popup_info['status'] == 'CAN_ACQUIRE'): # 可以领取饲料
            link_url = urllib.parse.urlparse(popup_info['linkUrl'])
            query = urllib.parse.parse_qs(link_url.query)
            if 'activityId' in query and len(query['activityId']) > 0:
                print('可以领取活动', query['activityId'][0], '的饲料...')
                alipay_mobile_aggrbillinfo_lottery_record_fodder_receive(s, query['activityId'][0])

        sheep_info = alipay_mobile_aggrbillinfo_sheep_info(s)
        if 'needFeedTimes' in sheep_info_extra and 'availableFodder' in sheep_info:
            need_feed_times = int(sheep_info_extra['needFeedTimes'])
            available_fodder = int(sheep_info['availableFodder'])
            print('当前还需要喂', need_feed_times, '次羊才能领羊奶，剩余饲料：', available_fodder)
            while True:
                if need_feed_times <= 0: # 可以领羊奶
                    print('可以领羊奶了！')
                    milk_info = alipay_mobile_aggrbillinfo_sheep_collect_milk(s)
                    if ('success' in milk_info
                        and milk_info['success']
                        and 'needFeedTimes' in milk_info):
                        need_feed_times = int(milk_info['needFeedTimes'])
                        print('成功领取羊奶，当前还需要喂', need_feed_times, '次羊才能再领羊奶！')
                    elif 'errorMsg' in milk_info:
                        print('领取羊奶失败：', milk_info['errorMsg'])
                        break
                    else:
                        print('领取羊奶失败！')
                        break

                if available_fodder < 100: # 剩余饲料不够喂羊
                    print('剩余饲料不足以喂羊！')
                    break

                feed_times = available_fodder / 100
                if feed_times > need_feed_times:
                    feed_times = need_feed_times

                feed_fodder = 100
                if feed_times >= 10:
                    feed_fodder = 1000

                feed_ret = alipay_mobile_aggrbillinfo_sheep_feed(s, feed_fodder)
                if ('success' in feed_ret
                    and feed_ret['success']
                    and 'availableFodder' in feed_ret
                    and 'needFeedTimes' in feed_ret):
                    need_feed_times = int(feed_ret['needFeedTimes'])
                    available_fodder = int(feed_ret['availableFodder'])
                    print('喂', (feed_fodder // 10), '次羊，当前还需要喂', need_feed_times, '次羊才能领羊奶，剩余饲料：', available_fodder)
                elif 'errorMsg' in feed_ret:
                    print('喂羊失败：', feed_ret['errorMsg'])
                    break
                else:
                    print('喂羊失败！')
                    break

                if ('propsGiftBox' in feed_ret
                    and 'status' in feed_ret['propsGiftBox']
                    and 'giftBoxId' in feed_ret['propsGiftBox']
                    and feed_ret['propsGiftBox']['status'] == 'WAIT_OPEN'): # 可以开宝箱
                    open_box(s, feed_ret['propsGiftBox']['giftBoxId'])

                if 'needFeedTimes' in feed_ret and 'availableFodder' in feed_ret:
                    need_feed_times = int(feed_ret['needFeedTimes'])
                    available_fodder = int(feed_ret['availableFodder'])
                    print('当前还需要喂', need_feed_times, '次羊才能领羊奶，剩余饲料：', available_fodder)

            # 兑换羊奶为现金
            withdraw_list = alipay_mobile_aggrbillinfo_withdraw_index(s)
            if ('goldNumStr' in withdraw_list
                and 'activityInfos' in withdraw_list
                and len(withdraw_list['activityInfos']) > 0):
                # 当前持有的羊奶数量
                gold_num = int(withdraw_list['goldNumStr'].replace(',', ''))

                most_gold_num = 0 # 兑换最高现金需要的羊奶数量
                most_activity_type = None
                for withdraw in withdraw_list['activityInfos']:
                    if ('goldNum' in withdraw
                        and 'activityType' in withdraw
                        and most_gold_num <= withdraw['goldNum']
                        and gold_num >= withdraw['goldNum']):
                        most_gold_num = withdraw['goldNum']
                        most_activity_type = withdraw['activityType']

                if most_activity_type is not None:
                    withdraw_ret = alipay_mobile_aggrbillinfo_withdraw_withdraw(s, most_activity_type)
                    if ('success' in withdraw_ret
                        and withdraw_ret['success']
                        and 'topText' in withdraw_ret
                        and 'transId' in withdraw_ret
                        and 'withdrawMoneyStr' in withdraw_ret):
                        print(withdraw_ret['topText'], '成功兑换金额：', withdraw_ret['withdrawMoneyStr'])

                        alipay_mobile_aggrbillinfo_withdraw_result(s, withdraw_ret['transId'])
                    elif 'errorMsg' in withdraw_ret:
                        print('兑换羊奶为现金失败：', withdraw_ret['errorMsg'])
                    else:
                        print('兑换羊奶为现金失败！')

        print('已经完成喂羊和领羊奶！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    # TODO 以下功能需要破解支付宝
    # TODO 在支付宝才能完成的领饲料任务
    # TODO 在支付宝才能完成的领金币任务
    # TODO 自动雇佣绵羊打工
    # TODO 自动领取打工金币
    # TODO 自动使用金币兑换支付红包

    #################################################################################################################################################

    while True:
        print('查看发现页面并开宝箱...')

        max_share_pages = 5 # 每天总共 5 个宝箱
        for i in range(1, max_share_pages + 1):
            # TODO 暂时不知道 remainTime 参数的用途，页面定时刷新倒计时？
            share_list = alipay_mobile_aggrbillinfo_share_square(s, 1, 20, random.randint(0, 300))
            if ('propsGiftBox' in share_list
                and 'status' in share_list['propsGiftBox']
                and 'giftBoxId' in share_list['propsGiftBox']
                and share_list['propsGiftBox']['status'] == 'WAIT_OPEN'): # 可以开宝箱
                open_box(s, share_list['propsGiftBox']['giftBoxId'])

        print('已经完成查看发现页面并开宝箱！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    while True:
        print('查看开奖消息并沾好运...')

        opened = False
        msg_list = alipay_mobile_aggrbillinfo_message_box_list(s, 1, 20)
        if 'messageInfos' in msg_list:
            for msg in msg_list['messageInfos']:
                if 'messageId' in msg and 'extInfo' in msg:
                    print('正在查看 ID 为', msg['messageId'], '的开奖消息并沾好运...')
                    ext_info = dict()
                    try:
                        ext_info = json.loads(msg['extInfo'])
                    except Exception:
                        traceback.print_exc()
                        print('!' * 120, '\n', msg['extInfo'], '\n' + '!' * 120)
                        continue

                    if 'activityId' in ext_info:
                        open_ret = alipay_mobile_aggrbillinfo_lottery_record_open_detail(s, ext_info['activityId'])
                        if 'successRecords' in open_ret:
                            for record in open_ret['successRecords']:
                                if 'status' in record and record['status'] == 'SUCCESS' and not opened:
                                    opened = True
                                    print('*' * 120 + '\n' + '*' * 120)
                                    print('*' * 5 + '恭喜你中奖了！！！请给我的脚本多多支持！！！' + '*' * 5)
                                    print('*' * 5 + 'https://github.com/tzwsoho/auto_snail_lucky' + '*' * 5)
                                    print('*' * 120 + '\n' + '*' * 120)
                                    webbrowser.open('https://github.com/tzwsoho/auto_snail_lucky', new = 0, autoraise = True)

                        if 'luckyDogsNew' in open_ret:
                            for lucky_dog in open_ret['luckyDogsNew']:
                                if ('propsGiftBox' in lucky_dog
                                    and 'giftBoxId' in lucky_dog['propsGiftBox']):
                                    open_box(s, lucky_dog['propsGiftBox']['giftBoxId'])
                        elif ('lotteryOpenDetailRedEnvelopeVo' in open_ret
                            and 'userVoList' in open_ret['lotteryOpenDetailRedEnvelopeVo']):
                            for lucky_dog in open_ret['lotteryOpenDetailRedEnvelopeVo']['userVoList']:
                                if ('propsGiftBox' in lucky_dog
                                    and 'giftBoxId' in lucky_dog['propsGiftBox']):
                                    open_box(s, lucky_dog['propsGiftBox']['giftBoxId'])

        print('已经完成查看开奖消息并沾好运！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    while True:
        print('开始每日抽满 500 次领最高 9000g 饲料...')

        item_list = None
        while True:
            fodder_popup = alipay_mobile_aggrbillinfo_sheep_fodder_popup(s)
            if ('canAcquireFodder' not in fodder_popup
                or 'fodderNumStr' not in fodder_popup
                or 'status' not in fodder_popup
                or 'needLotteryCountStr' not in fodder_popup
                or fodder_popup['needLotteryCountStr'] == ''
                or int(fodder_popup['canAcquireFodder']) >= 9000):
                break

            fodder_toast = ''
            if fodder_popup['status'] == 'CAN_ACQUIRE':
                fodder_toast = '当前可领取 ' + fodder_popup['canAcquireFodder'] + 'g 饲料！'
            elif fodder_popup['status'] == 'NORMAL':
                fodder_toast = '再抽奖 ' + fodder_popup['needLotteryCountStr'] + ' 次可领取 ' + fodder_popup['needLotteryCountStr'] + 'g 饲料！'
            elif fodder_popup['status'] == 'MODULUS_TOP':
                fodder_toast = '当前可领取 ' + fodder_popup['canAcquireFodder'] + 'g 饲料，再抽奖 ' + \
                    fodder_popup['needLotteryCountStr'] + ' 次可多领取 ' + fodder_popup['fodderNumStr'] + 'g 饲料！'
            print(fodder_toast)

            sign_list = alipay_mobile_aggrbillinfo_user_sign_list(s)
            if 'cateConfs' in sign_list:
                # 准备足够羊毛并获取羊毛信息
                available_quota, limit_quota = prepare_wool(s)
                if available_quota > 0:
                    need_lottery_count = 100
                    if fodder_popup['status'] != 'MODULUS_TOP':
                        need_lottery_count = int(fodder_popup['needLotteryCountStr'])

                    for _ in range(0, need_lottery_count):
                        if item_list is None or len(item_list) <= 0:
                            item_list = collect_lottery_items_info(s, sign_list['cateConfs'])

                        # 从最低价商品开始抽奖
                        item = item_list[0]
                        item_list.remove(item)

                        if item is None:
                            break

                        available_quota, limit_quota = lottery(s, item, available_quota)
                        if available_quota <= 0:
                            break
                else:
                    print('当前羊毛不足以抽奖，请过段时间再来...')
                    break

        print('已经完成每日抽满 500 次，明日可领最高 9000g 饲料！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    while True:
        print('开始参加抽大奖活动...')

        # 根据抽奖限额搜索商品信息
        def binary_search(lst, quota):
            if len(lst) == 0:
                return None

            left = 0
            right = len(lst) - 1
            while left <= right:
                mid = left + (right - left) // 2
                if lst[mid]['salePrice'] == quota:
                    break
                elif lst[mid]['salePrice'] > quota: # 在较低价区搜索
                    right = mid - 1
                elif lst[mid]['salePrice'] < quota: # 在较高价区搜索
                    left = mid + 1

            if lst[mid]['salePrice'] > quota and mid > 0:
                return lst[mid - 1]
            else:
                return lst[mid]

        item_list = None

        # 商品类型，可以修改 sign_list['cateConfs'] 实现只对某些类型的商品进行抽奖
        sign_list = alipay_mobile_aggrbillinfo_user_sign_list(s)
        if 'cateConfs' in sign_list:
            # 开始抽奖
            while True:
                # 准备足够羊毛并获取羊毛信息
                available_quota, limit_quota = prepare_wool(s)

                # 收取羊毛、使用卡片之后仍不足以符合抽奖需求
                if available_quota < limit_quota:
                    print('可用羊毛只有', available_quota, '不够抽奖，请过段时间再来...')
                    break

                retried = False
                while True:
                    item = None

                    # 获取商品列表
                    if item_list is None or len(item_list) <= 0:
                        item_list = collect_lottery_items_info(s, sign_list['cateConfs'])

                    #########################################################################################################
                    # 从最高可抽的商品开始抽奖
                    #########################################################################################################

                    # 计算可抽奖商品价格上限
                    quota = available_quota
                    if available_quota > limit_quota:
                        quota = limit_quota

                    # 只对高价商品抽奖
                    if quota < limit_quota:
                        print('羊毛不够了...')
                        break

                    # 搜索符合条件的商品
                    while (item_list is not None) and (len(item_list) > 0):
                        item = binary_search(item_list, quota)
                        if item is not None:
                            item_list.remove(item)
                            if item['salePrice'] <= quota:
                                break

                    #########################################################################################################
                    # 从最低价商品开始抽奖
                    #########################################################################################################

                    # item = item_list[0]
                    # item_list.remove(item)

                    #########################################################################################################

                    if item is None:
                        print('没有符合抽奖条件的商品！')
                        if retried:
                            item_list = None
                            break

                        retried = True
                        continue
                    elif item['salePrice'] > available_quota:
                        print('羊毛不足！', item)
                        break

                    retried = False
                    available_quota, limit_quota = lottery(s, item, available_quota)

        print('已经完成抽大奖活动！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    while True:
        print('开始参加组团抽奖活动...')

        # 新版本的活动参与次数卡的数量就是剩余抽奖次数
        # print('尝试自动使用活动参与次数卡...')
        # prop_ret = alipay_mobile_aggrbillinfo_sheep_prop_list(s)
        # if 'propVoList' in prop_ret:
        #     for prop in prop_ret['propVoList']:
        #         if 'desc' in prop and 'type' in prop:
        #             re_ret = re.search('活动参与次数\\+(\\d+)', prop['desc'])
        #             if re_ret is not None:
        #                 print('使用一张', prop['desc'], '卡片...')
        #                 use_ret = alipay_mobile_aggrbillinfo_props_card_use(s, 1, prop['type'])
        #                 if ('success' in use_ret
        #                     and 'toastTxt' in use_ret
        #                     and use_ret['success']):
        #                     print(use_ret['toastTxt'])
        #                 elif 'errorMsg' in use_ret:
        #                     print('卡片使用失败：', use_ret['errorMsg'])
        #                     break
        #                 else:
        #                     print('卡片使用失败！')
        #                     break

        sign_list = alipay_mobile_aggrbillinfo_user_sign_list(s)
        if ('duplicateActivityVos' in sign_list
            and len(sign_list['duplicateActivityVos']) == 1
            and 'activityStatus' in sign_list['duplicateActivityVos'][0]
            and 'activityName' in sign_list['duplicateActivityVos'][0]
            and 'activityType' in sign_list['duplicateActivityVos'][0]
            and sign_list['duplicateActivityVos'][0]['activityStatus'] == 'INIT'): # 正在进行的组团抽奖活动
            print(sign_list['duplicateActivityVos'][0]['activityName'], '...')

            duplicate_activity_type = sign_list['duplicateActivityVos'][0]['activityType']
            tab_list = alipay_mobile_aggrbillinfo_duplicate_tab(s, duplicate_activity_type, 1, 100)
            if 'userPropNum' in tab_list and 'indexItemVoList' in tab_list:
                user_prop_num = int(tab_list['userPropNum'])
                if user_prop_num <= 0:
                    print('抽奖次数不足！')
                else:
                    for i in range(0, len(tab_list['indexItemVoList'])):
                        item = tab_list['indexItemVoList'][i]
                        if ('activityId' in item
                            and 'itemId' in item
                            and 'itemType' in item
                            and 'title' in item):
                            if ('status' not in item) or (item['status'] != 'FINISHED'):
                                status_info = alipay_mobile_aggrbillinfo_duplicate_lottery_status(s, item['activityId'], duplicate_activity_type, item['itemId'], item['itemType'])
                                if 'userPropNum' in status_info:
                                    user_prop_num = int(status_info['userPropNum'])
                                    if user_prop_num <= 0:
                                        print('抽奖次数已用完！')
                                        break

                                print('开始组团抽奖，剩余抽奖次数：', user_prop_num, '商品为', item['title'])
                                lottery_ret = alipay_mobile_aggrbillinfo_duplicate_lottery(s, item['activityId'], duplicate_activity_type, item['itemId'], item['itemType'])
                                if 'lotteryRecordId' in lottery_ret: # 继续进行摇一摇
                                    yaoyiyao_ret = alipay_mobile_aggrbillinfo_duplicate_group_yaoyiyao(s, item['activityId'], lottery_ret['lotteryRecordId'])
                                    if 'memberTotal' in yaoyiyao_ret and 'lotteryCode' in lottery_ret:
                                        print('已参加商品', item['title'], '的组团抽奖',
                                            '组团人数：', yaoyiyao_ret['memberTotal'],
                                            '抽奖幸运号码：', lottery_ret['lotteryCode'])
                        else:
                            print('商品信息有误：', item)
        else:
            print('目前没有正在进行的组团抽奖活动！')

        print('已经完成组团抽奖活动！', '\n' + '*' * 120)
        break

    #################################################################################################################################################

    print('所有任务已完成！')
    sys.exit(0)

    #################################################################################################################################################

max_functions = 11
functions = set()
print('请点击几羊 APP 内的任意链接，本代码共需要收集', max_functions, '个函数或类实例的相关信息...')

def on_message(message, payload):
    if message['type'] != 'send':
        return

    if ((message['payload'] >= 1) or (message['payload'] <= max_functions)):
        functions.add(message['payload'])
        print('已收集 ' + str(len(functions)) + '/' + str(max_functions) + ': ' + str(functions))
        if len(functions) == max_functions:
            print('函数或类实例已经收集完毕！', '\n' + '*' * 120)
            _thread.start_new_thread(on_ready, (script,))

script.on('message', on_message)
script.load()

input() # 等待输入

session.detach()
