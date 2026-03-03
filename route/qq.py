import json
import os
import re
import time

import requests
from flask import request, Blueprint

import ai
from config import qq as qq_conf, match, cq_speech_md5_pattern
from logger import logger
from plugin.recog import get_speech_text, recog_voices_path
from plugin.reply import send_private, send_group
from plugin.tts import tts_url, tts_cos

qq_api = Blueprint("qq_api", __name__)
cq_http_url = qq_conf['cq-http-url']  # CQ-http地址
# @QQ号与昵称，因为有时是复制的@，所以有可能是@昵称
at_qq = f"[CQ:at,qq={qq_conf['uid']}]"
at_nickname = f"@{qq_conf['nickname']}"
group_speech_reply = qq_conf['group-speech-reply']
private_white_list = qq_conf['private-white-list']


@qq_api.route('/', methods=['POST'])
def receive():
    req_json = request.get_json()
    message = req_json.get('raw_message')
    _speech, _ = match(cq_speech_md5_pattern, message)
    if _speech and group_speech_reply:
        message = get_speech_text(get_record(_speech[0]))
    if req_json.get('message_type') == 'private':  # 私聊信息
        uid = req_json.get('sender').get('user_id')
        if (private_white_list and uid in private_white_list) or not private_white_list:
            logger.info(f"[qq]私聊-{uid}:{message}")
            msg_text = ai.main(uid, message, 'qq')
            send_private(uid, msg_text)
    elif req_json.get('message_type') == 'group':  # 群消息
        gid = req_json.get('group_id')  # 群号
        uid = req_json.get('sender').get('user_id')
        logger.info(f"[qq]群聊-{uid}:{message}")
        if at_qq in message or at_nickname in message or _speech:  # 被@时才回答
            if not _speech:
                message = message.replace(at_qq, "", 1)
                message = message.replace(at_nickname, "", 1)
                message = message.strip()
            if message[0] != "#":
                message = f"[用户{uid}]说:" + message
            msg_text = ai.main(gid, message, 'qq', True)
            send_group(gid, uid, msg_text)
    return json.dumps({
        "msg": "ok"
    })


def _get_target(url, params, retry=3):
    err_num = 0
    while True:
        res = requests.get(url=url, params=params).json()
        if res["status"] == "ok":
            break
        if "not found" not in res.get('data', {}).get('error', '') or err_num > retry:
            return None
        err_num += 1
        logger.warn(f"[qq]_get_target retry {err_num}")
        time.sleep(1)
    return res


def get_record(file_md5):
    """
    获取语音
    """
    res = _get_target(cq_http_url + "/get_record", {'file': file_md5, 'out_format': 'amr'})
    if res is None:
        return None
    file_url = res['data']['url']
    download_url = cq_http_url + file_url
    local_path = recog_voices_path + file_url
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    download_res = requests.get(download_url)
    if download_res.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(download_res.content)
            return file_url
    return None
