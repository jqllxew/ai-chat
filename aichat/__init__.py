import aiimage
from config import chat as chat_conf, display
from .chat_ai import ChatAI
from .open_ai import OpenAI

user_models: dict[str, ChatAI] = {}


def u_model(uid, from_type=None, need_ctx=True):
    m = user_models.get(uid)
    if m is None:
        openai_conf = display(chat_conf['openai'])
        if openai_conf is not None:
            m = OpenAI(
                api_key=openai_conf['api-key'],
                uid=uid,
                max_req_length=openai_conf['max-req-length'],
                max_resp_tokens=openai_conf['max-resp-tokens'],
                from_type=from_type,
                need_ctx=need_ctx)
            user_models[uid] = m
    return m


def chat(uid: str, query: str, from_type: str):
    query = query.strip()
    if query[0] == "画":
        return aiimage.draw(uid, query[1:], from_type)
    return u_model(uid, from_type).reply(query)


__all__ = [
    "chat",
    "u_model",
    "ChatAI",
    "OpenAI",
]
