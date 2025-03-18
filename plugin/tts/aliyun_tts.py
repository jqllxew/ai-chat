# -*- coding: UTF-8 -*-
import http.client
import json
import os
import time
from urllib.parse import quote_plus
from config import plugin as plugin_conf, display
from plugin import tx_cos
from plugin.tts.aliyun_token import get_token

tts_conf = plugin_conf['tts']
app_key = display(tts_conf['aliyun']['app-key'])
host = 'nls-gateway-cn-shanghai.aliyuncs.com'
url = 'https://' + host + '/stream/v1/tts'


def tts(text, cos_key=None, local_key=None, _format='wav', _sample_rate=16000):
    headers = {
        'Content-Type': 'application/json'
    }
    body = json.dumps({
        'appkey': app_key,
        'token': get_token(),
        'text': text,
        'format': _format,
        'sample_rate': _sample_rate
    })
    conn = http.client.HTTPSConnection(host)
    conn.request(method='POST', url=url, body=body, headers=headers)
    resp = conn.getresponse()
    try:
        if 'audio/mpeg' != resp.getheader('Content-Type'):
            return None
        if local_key:
            parent_dir = os.path.dirname(local_key)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            with open(local_key, mode='wb') as f:
                f.write(resp.read())
            key = local_key
        elif cos_key:
            key = tx_cos.upload(cos_key, resp.read())
        else:
            raise RuntimeError('')
        return key
    finally:
        conn.close()


def tts_cos(text, uid, _format='mp3'):
    prefix = tx_cos.store_dir('audio')
    cos_key = f"{prefix}/{uid}/{int(time.time()*1000)}.{_format}"
    return tts(text, cos_key=cos_key, _format=_format)


def tts_url(text, _format='mp3', _sample_rate=16000):
    text = quote_plus(text)
    text = text.replace("+", "%20")
    text = text.replace("*", "%2A")
    text = text.replace("%7E", "~")
    _url = url + '?appkey=' + app_key
    _url = _url + '&token=' + get_token()
    _url = _url + '&text=' + text
    _url = _url + '&format=' + _format
    _url = _url + '&sample_rate=' + str(_sample_rate)
    # voice 发音人，可选，默认是xiaoyun。
    # _url = _url + '&voice=' + 'xiaoyun'
    # volume 音量，范围是0~100，可选，默认50。
    # _url = _url + '&volume=' + str(50)
    # speech_rate 语速，范围是-500~500，可选，默认是0。
    # _url = _url + '&speech_rate=' + str(0)
    # pitch_rate 语调，范围是-500~500，可选，默认是0。
    # _url = _url + '&pitch_rate=' + str(0)
    return _url
