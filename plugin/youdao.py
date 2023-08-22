import json
import uuid
import requests
import hashlib
import time
from config import fanyi as fanyi_conf

youdao_conf = fanyi_conf['youdao']
app_key = youdao_conf['app-key']
app_secret = youdao_conf['app-secret']
youdao_url = 'https://openapi.youdao.com/api'


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


def do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(youdao_url, data=data, headers=headers)


def _translation(q, _from, to):
    data = {'from': _from, 'to': to, 'signType': 'v3'}
    cur_time = str(int(time.time()))
    data['curtime'] = cur_time
    salt = str(uuid.uuid1())
    signStr = app_key + truncate(q) + salt + cur_time + app_secret
    sign = encrypt(signStr)
    data['appKey'] = app_key
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign
    # data['vocabId'] = "您的用户词表ID"
    response = do_request(data)
    # contentType = response.headers['Content-Type']
    # if contentType == "audio/mp3":
    #     millis = int(round(time.time() * 1000))
    #     filePath = "合成的音频存储路径" + str(millis) + ".mp3"
    #     fo = open(filePath, 'wb')
    #     fo.write(response.content)
    #     fo.close()
    # else:
    ret = json.loads(response.content)
    if ret.get('translation') is not None:
        return ret['translation'][0]
    return ''


def chs2en(q):
    try:
        return _translation(q, _from='zh-CHS', to='en')
    except Exception:
        return q


if __name__ == '__main__':
    print(_translation(q='可爱', _from='zh-CHS', to='en'))
