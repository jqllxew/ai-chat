import requests
from flask import request, Blueprint

import aichat
from config import qq as qq_conf
from logger import logger

qq_api = Blueprint("qq_api", __name__)
cq_http_url = qq_conf['cq-http-url']  # CQ-http地址
# @QQ号与昵称，因为有时是复制的@，所以有可能是@昵称
at_qq = f"[CQ:at,qq={qq_conf['uid']}]"
at_nickname = f"@{qq_conf['nickname']}"


@qq_api.route('/', methods=['POST'])
def receive():
    req_json = request.get_json()
    if req_json.get('message_type') == 'private':         # 私聊信息
        uid = req_json.get('sender').get('user_id')
        message = req_json.get('raw_message')
        logger.info(f"[qq]私聊-{uid}:{message}")
        msg_text = aichat.chat(uid, message, 'qq')  # 将消息转发给AI处理
        send_private(uid, msg_text)
    elif req_json.get('message_type') == 'group':         # 群消息
        gid = req_json.get('group_id')                    # 群号
        uid = req_json.get('sender').get('user_id')
        message = req_json.get('raw_message')
        logger.info(f"[qq]群聊-{uid}:{message}")
        if at_qq in message or at_nickname in message:    # 被@时才回答
            message = message.replace(at_qq, "", 1)
            message = message.replace(at_nickname, "", 1)
            msg_text = aichat.chat(uid, message, 'qq')
            msg_text = f"[CQ:at,qq={uid}]\n" + msg_text
            send_group(gid, msg_text)
    if req_json.get('post_type') == 'request':
        request_type = req_json.get('request_type')       # group
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
    return "ok"


def send_private(uid, message):
    res = requests.post(url=cq_http_url + "/send_private_msg",
                        params={'user_id': int(uid), 'message': message}).json()
    if res.get('status') != "ok":
        logger.warn(f"[qq]send_private err:{res}")


def send_group(gid, message):
    res = requests.post(url=cq_http_url + "/send_group_msg",
                        params={'group_id': int(gid), 'message': message}).json()
    if res["status"] != "ok":
        logger.warn(f"[qq]send_group err:{res}")


def handle_friend_add(flag, approve):
    res = requests.post(url=cq_http_url + "/set_friend_add_request",
                        params={'flag': flag, 'approve': approve}).json()
    if res["status"] != "ok":
        logger.warn(f"[qq]handle_friend_add err:{res}")


def handle_group_invite(flag, approve):
    res = requests.post(url=cq_http_url + "/set_group_add_request",
                        params={'flag': flag, 'sub_type': 'invite', 'approve': approve}).json()
    if res["status"] != "ok":
        logger.warn(f"[qq]handle_group_invite err:{res}")
