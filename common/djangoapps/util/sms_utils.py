# -*- coding: UTF-8 -*-
"""
Utilities for SMS manipulation.
"""
import json
import random
import requests
from django.conf import settings


def send_urgent_short_message(destnumbers, msg, sendtime, channel=1):
    """
    发送紧急短信.特点是速度快，通常用来发送验证码，账号密码等信息
    :param destnumbers: 发送号码最大一次提交200个,号码用任意分隔符分开，发送号码移动,联通,小灵通可以混和提交
    :param msg: 发送内容最大250个字符,不分区中英文
    :param sendtime: 【时间功能暂不可用】发送时间 不加sendtime参数或值为“”时短信立即发送,如果要定制发送时间则加sendtime参数格式为 YYYY-MM-DD HH:MM:SS 如:2008-05-12 10:00:00
    :param channel: 1-签名"英荔教育"，2-签名"E教育"，默认通道是1
    :return: 实际需返回是否发送成功/失败，以及原因
    """
    return_msg_str = ''  # 返回消息
    user_id = settings.SMS_API['urgent_auth']['userid'].encode('utf8')
    password = settings.SMS_API['urgent_auth']['password'].encode('utf8')
    destnumbers_utf8 = destnumbers.encode('utf8')

    if int(channel) == 1:
        msg = msg + "【英荔教育】"
    elif int(channel) == 2:
        msg = msg + "【E教育】"
        return False, '此短信通道已经关闭'

    msg_utf8 = msg.encode('utf8')
    sendtime_utf8 = sendtime.encode('utf8').replace('T', '+')

    msgid = random.randint(11111111, 99999999)
    data = {
        "id": msgid,
        "method": "send",
        "params": {
            "userid": user_id,
            "password": password,
            "submit": [{
                "content": msg_utf8,
                "phone": destnumbers_utf8
            }]
        }
    }
    payload = json.dumps(data)
    headers = {
        'cache-control': "no-cache"
    }
    url = settings.SMS_API_URL

    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        response_json = json.loads(response.text)
        count = 0
        success_count = 0
        for result in response_json['result']:
            count = count + 1
            if int(result['return']) == 0:
                success_count = success_count + 1
            else:
                return_msg_str = return_msg_str + result['info'] + ','

        if count == success_count:
            # 成功
            success = True
            return_msg_str = '短信已发送'
        else:
            # 错误
            success = False
            return_msg_str = return_msg_str[:-1]
    except Exception as e:
        success = False
        return_msg_str = return_msg_str[:-1]

    return success, return_msg_str


def send_short_message(destnumbers, msg, sendtime, channel=1):
    """
        发送普通短信.通常用来促销，学习提醒等信息
        :param destnumbers: 发送号码最大一次提交200个,号码用任意分隔符分开，发送号码移动,联通,小灵通可以混和提交
        :param msg: 发送内容最大250个字符,不分区中英文
        :param sendtime: 【时间功能暂不可用】发送时间 不加sendtime参数或值为“”时短信立即发送,如果要定制发送时间则加sendtime参数格式为 YYYY-MM-DD HH:MM:SS 如:2008-05-12 10:00:00
        :param channel: 1-签名"英荔教育"，2-签名"E教育"，默认通道是1
        :return: 实际需返回是否发送成功/失败，以及原因
        """
    return_msg_str = ''  # 返回消息
    user_id = settings.SMS_API['normal_auth']['userid'].encode('utf8')
    password = settings.SMS_API['normal_auth']['password'].encode('utf8')
    destnumbers_utf8 = destnumbers.encode('utf8')

    if int(channel) == 1:
        msg = msg + "【英荔教育】"
    elif (channel) == 2:
        msg = msg + "【E教育】"
        return False, '此短信通道已经关闭'

    msg_utf8 = msg.encode('utf8')
    sendtime_utf8 = sendtime.encode('utf8').replace('T', '+')

    msgid = random.randint(11111111, 99999999)
    data = {
        "id": msgid,
        "method": "send",
        "params": {
            "userid": user_id,
            "password": password,
            "submit": [{
                "content": msg_utf8,
                "phone": destnumbers_utf8
            }]
        }
    }
    payload = json.dumps(data)
    headers = {
        'cache-control': "no-cache"
    }
    url = settings.SMS_API_URL

    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        response_json = json.loads(response.text)
        count = 0
        success_count = 0
        for result in response_json['result']:
            count = count + 1
            if int(result['return']) == 0:
                success_count = success_count + 1
            else:
                return_msg_str = return_msg_str + result['info'] + ','

        if count == success_count:
            # 成功
            success = True
            return_msg_str = '短信已发送'
        else:
            # 错误
            success = False
            return_msg_str = return_msg_str[:-1]
    except Exception as e:
        success = False
        return_msg_str = return_msg_str[:-1]

    return success, return_msg_str


def send_short_message_by_linkgroup(destnumbers, msg, sendtime='', channel=1):
    """
        通过凌凯集团发送短信
        :param destnumbers: 发送号码最大一次提交500个,号码用英文逗号隔开。
        :param msg: 发送的内容。
        :param sendtime: sendtime参数格式为 YYYY-MM-DD HH:MM:SS 如:2008-05-12 10:00:00 或者为空。
        :param Cell: 扩展号(必须是数字或为空)。
        :param channel: 1-签名【E-ducation】。
        :return: 实际需返回是否发送成功/失败，以及原因
        """
    CorpID = settings.SMS_API_BY_LINKGROUP['normal_auth']['userid']  # 账号
    Pwd = settings.SMS_API_BY_LINKGROUP['normal_auth']['password']   # 密码
    Mobile = destnumbers
    Content = msg.decode('utf-8').encode('gb2312')
    if sendtime:
        SendTime = sendtime.strftime('%Y%m%d%H%m%S')
    else:
        SendTime = ''

    data = {
        'CorpID': CorpID,
        'Pwd': Pwd,
        'Mobile': Mobile,
        'Content': Content,
        'Cell': '',
        'SendTime': SendTime
    }
    headers = {
        'cache-control': "no-cache"
    }
    url = settings.SMS_API_URL_BY_LINKGROUP

    try:
        response = requests.request('GET', url, params=data, headers=headers)
        if int(response.text) > 0:
            success = True
            return_msg_str = '短信已发送'
        else:
            success = False
            return_msg_str = '短信发送失败'
    except Exception as e:
        success = False
        return_msg_str = '短信发送失败'

    return success, return_msg_str
