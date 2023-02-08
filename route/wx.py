from flask import request, Blueprint

from aichat import chat_factory
from config import wx as wx_conf

wx_api = Blueprint(name="wx_api", import_name=__name__, url_prefix='/wx')
at_nickname = f"@{wx_conf['nickname']}"


@wx_api.route('/', methods=['post'])
def receive():
    req_json = request.get_json()
    uid = req_json['payload']['id']
    name = req_json['payload']['name']
    message = req_json['text']
    room = req_json.get('room')
    if room and room != 'undefined':
        if at_nickname in message:
            print(f"[wx]群聊：{name}\n{message}")
            message = message.replace(at_nickname, "", 1)
            msg_text = chat_factory.chat(uid, message, 'wx')
            msg_text = f"@{name}\n" + msg_text
        else:
            msg_text = ""
    else:
        print(f"[wx]私聊：{name}\n{message}")
        msg_text = chat_factory.chat(uid, message, 'wx')
    return msg_text
