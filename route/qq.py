import json
import os
import re
import time

import requests
from flask import request, Blueprint

import aichat
from config import qq as qq_conf, match, cq_speech_md5_pattern
from logger import logger
from plugin import speech_recog
from plugin.tts import tts_url, tts_cos

qq_api = Blueprint("qq_api", __name__)
cq_http_url = qq_conf['cq-http-url']  # CQ-http地址
# @QQ号与昵称，因为有时是复制的@，所以有可能是@昵称
at_qq = f"[CQ:at,qq={qq_conf['uid']}]"
at_nickname = f"@{qq_conf['nickname']}"
group_session = qq_conf['group-session']
group_speech_reply = qq_conf['group-speech-reply']
private_white_list = qq_conf['private-white-list']


@qq_api.route('/', methods=['POST'])
def receive():
    req_json = request.get_json()
    message = req_json.get('raw_message')
    _speech, _ = match(cq_speech_md5_pattern, message)
    if _speech and group_speech_reply:
        message = speech_recog.get_speech_text(get_record(_speech[0]))
    if req_json.get('message_type') == 'private':  # 私聊信息
        uid = req_json.get('sender').get('user_id')
        if (private_white_list and uid in private_white_list) or not private_white_list:
            logger.info(f"[qq]私聊-{uid}:{message}")
            msg_text = aichat.chat(uid, message, 'qq')
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
            _id = gid if group_session else uid
            if message[0] != "#":
                message = f"[用户{uid}]说:" + message
                msg_text = aichat.chat(_id, message, 'qq')
            else:
                msg_text = aichat.chat(_id, message, 'qq')
            send_group(gid, uid, msg_text)
    elif req_json.get('post_type') == 'request':
        request_type = req_json.get('request_type')  # group
        uid = req_json.get('user_id')
        flag = req_json.get('flag')
        comment = req_json.get('comment')
        if request_type == "friend":
            logger.info(f"[qq]好友申请:{uid} 验证信息:{comment}")
            handle_friend_add(flag, "true")
        if request_type == "group":
            sub_type = req_json.get('sub_type')
            gid = req_json.get('group_id')
            if sub_type == "add":
                logger.info(f"[qq]加群申请:{uid} 验证信息:{comment}")
            elif sub_type == "invite":
                logger.info(f"[qq]邀请进群:{uid} 群号:{gid}")
                handle_group_invite(flag, "true")
    return json.dumps({
        "msg": "ok"
    })


def _find_ssml(text):
    match = re.search(r'<speak.+?>.*?</speak>', text, flags=re.DOTALL)
    return match.group() if match else None


def send_private(uid, message):
    ssml = _find_ssml(message)
    if ssml:
        if len(ssml) < 127:
            msg_text = f"[CQ:record,file={tts_url(ssml)}]"
        else:
            msg_text = f"[CQ:record,file={tts_cos(ssml, uid)}]"
    else:
        msg_text = message
    res = requests.post(url=cq_http_url + "/send_private_msg",
                        data={'user_id': int(uid), 'message': msg_text}).json()
    if res.get('status') != "ok":
        logger.warn(f"[qq]send_private err:{res}")


def send_group(gid, uid, message):
    ssml = _find_ssml(message)
    if ssml:
        if len(ssml) < 127:
            msg_text = f"[CQ:record,file={tts_url(ssml)}]"
        else:
            msg_text = f"[CQ:record,file={tts_cos(ssml, uid)}]"
    else:
        msg_text = f"[CQ:at,qq={uid}]\n" + message
    res = requests.post(url=cq_http_url + "/send_group_msg",
                        data={'group_id': int(gid), 'message': msg_text}).json()
    if res["status"] != "ok":
        logger.warn(f"[qq]send_group err:{res}")


def handle_friend_add(flag, approve):
    res = requests.post(url=cq_http_url + "/set_friend_add_request",
                        data={'flag': flag, 'approve': approve}).json()
    if res["status"] != "ok":
        logger.warn(f"[qq]handle_friend_add err:{res}")


def handle_group_invite(flag, approve):
    res = requests.post(url=cq_http_url + "/set_group_add_request",
                        data={'flag': flag, 'sub_type': 'invite', 'approve': approve}).json()
    if res["status"] != "ok":
        logger.warn(f"[qq]handle_group_invite err:{res}")


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
    local_path = speech_recog.voices_base_path + file_url
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    download_res = requests.get(download_url)
    if download_res.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(download_res.content)
            return file_url
    return None
