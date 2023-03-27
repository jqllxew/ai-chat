import aiimage
from config import chat as chat_conf, display
from .chatai import ChatAI
from .gpt import OpenAI, ChatGPT

user_models: dict[str, ChatAI] = {}


def u_change_model(uid, chat_type='', from_type=None, need_ctx=True, need_ins=True, model_id=None) -> str:
    if 'gpt3.5' == chat_type or 'chatgpt' == chat_type:
        gpt35_conf = chat_conf['openai']['gpt3.5']
        user_models[uid] = ChatGPT(
            uid=uid,
            api_key=display(gpt35_conf['api-key']),
            max_req_length=display(gpt35_conf['max-req-length']),
            max_resp_tokens=display(gpt35_conf['max-resp-tokens']),
            proxy=display(gpt35_conf['proxy']),
            default_system=display(gpt35_conf['default-system']),
            from_type=from_type,
            model_id=model_id,
            need_ctx=need_ctx,
            need_ins=need_ins)
    elif 'gpt3'==chat_type:
        gpt3_conf = chat_conf['openai']['gpt3']
        user_models[uid] = OpenAI(
            uid=uid,
            api_key=display(gpt3_conf['api-key']),
            max_req_length=display(gpt3_conf['max-req-length']),
            max_resp_tokens=display(gpt3_conf['max-resp-tokens']),
            proxy=display(gpt3_conf['proxy']),
            from_type=from_type,
            model_id=model_id,
            need_ctx=need_ctx,
            need_ins=need_ins)
    else:
        return f"未找到 {chat_type}"


def u_model(uid, from_type=None, need_ctx=True, need_ins=True) -> ChatAI:
    if not user_models.get(uid):
        u_change_model(uid, 'gpt3.5', from_type, need_ctx, need_ins)
    return user_models.get(uid)


def chat(uid: str, query: str, from_type: str):
    query = query.strip()
    if query[0] == "画":
        return aiimage.draw(uid, query[1:], from_type)
    if query.find("#changechat") == 0:
        chat_type = query.replace("#changechat", "", 1).strip()
        err = u_change_model(uid, chat_type, from_type)
        return err or f"changed to {chat_type}"
    elif query.find("#changeimage") == 0:
        image_type = query.replace("#changeimage", "", 1).strip()
        err = aiimage.u_change_model(uid, image_type, from_type)
        return err or f"changed to {image_type}"
    reply, err = u_model(uid, from_type).reply(query)
    return err or reply


__all__ = [
    "chat",
    "u_model",
    "ChatAI",
    "OpenAI",
    "ChatGPT"
]
