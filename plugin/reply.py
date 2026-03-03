import re

import requests
from config import qq as qq_conf
from logger import logger
from plugin.tts.speechify_tts import speechify_tts

cq_http_url = qq_conf['cq-http-url']  # CQ-http地址


def _find_speech(text):
    pattern = re.compile(
        r'<speech\s+([^>]*)>(.*?)</speech>',
        flags=re.DOTALL
    )
    _match = pattern.search(text)
    if not _match:
        return None

    attr_str, content = _match.groups()
    attrs = dict(re.findall(r'(\w+)="([^"]+)"', attr_str))
    return {
        "pitch": _clamp_int(attrs.get("pitch")),
        "speed": _clamp_int(attrs.get("speed")),
        "prompt": attrs.get("prompt"),
        "text": content.strip()
    }


def _clamp_int(value, min_v=0, max_v=15, default=5):
    try:
        v = int(value)
        return max(min_v, min(max_v, v))
    except (TypeError, ValueError):
        return default


def send_private(uid, message):
    if message:
        res = requests.post(url=cq_http_url + "/send_private_msg",
                            headers={"Authorization": "Bearer jqllxew"},
                            data={'user_id': int(uid), 'message': message}).json()
        if res.get('status') != "ok":
            logger.warn(f"[qq]send_private err:{res}")
        speech = _find_speech(message)
        if speech and speech.get("text"):
            print(f"speech: {speech}")
            speech_qq = f"[CQ:record,file={speechify_tts(uid, **speech)}]"
            requests.post(url=cq_http_url + "/send_private_msg",
                          headers={"Authorization": "Bearer jqllxew"},
                          data={'user_id': int(uid), 'message': speech_qq}).json()


def send_group(gid, uid, message):
    if message:
        msg_text = f"[CQ:at,qq={uid}]\n{message}" if uid else message
        res = requests.post(url=cq_http_url + "/send_group_msg",
                            headers={"Authorization": "Bearer jqllxew"},
                            data={'group_id': int(gid), 'message': msg_text}).json()
        if res["status"] != "ok":
            logger.warn(f"[qq]send_group err:{res}")
        speech = _find_speech(message)
        if speech and speech.get("text"):
            speech_qq = f"[CQ:record,file={speechify_tts(uid, **speech)}]"
            requests.post(url=cq_http_url + "/send_group_msg",
                          headers={"Authorization": "Bearer jqllxew"},
                          data={'group_id': int(gid), 'message': speech_qq}).json()


def send(that, message):
    uid = getattr(that, "uid")
    is_group = getattr(that, "is_group")
    if is_group:
        send_group(gid=uid, uid=None, message=message)
    else:
        send_private(uid, message)