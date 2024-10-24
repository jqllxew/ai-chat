from flask import request, Blueprint

import aichat
from config import wx as wx_conf
from logger import logger

wx_api = Blueprint(name="wx_api", import_name=__name__, url_prefix='/wx')
at_nickname = f"@{wx_conf['nickname']}"


@wx_api.route('/', methods=['POST'])
def receive():
    req_json = request.get_json()
    uid = req_json['payload']['id']
    name = req_json['payload']['name']
    message = req_json['text']
    room = req_json.get('room')
    if room and room != 'undefined':
        room_id = room.get('id')
        if at_nickname in message:
            logger.info(f"[wx]{name}-群聊:{message}")
            message = message.replace(at_nickname, "", 1)
            msg_text = aichat.chat(room_id, message, 'wx')
            msg_text = f"@{name}\n" + msg_text
        else:
            msg_text = ""
    else:
        logger.info(f"[wx]{name}-私聊:{message}")
        msg_text = aichat.chat(uid, message, 'wx')
    return msg_text
