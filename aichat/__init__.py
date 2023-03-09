import aiimage
from config import chat as chat_conf, display
from .chatai import ChatAI
from .chatgpt import ChatGPT
from .open_ai import OpenAI

user_models: dict[str, ChatAI] = {}


def u_change_model(uid, chat_type='', from_type=None, need_ctx=True, need_ins=True, model_id=None) -> str:
    if 'openai-chatgpt'==chat_type or 'chatgpt' in chat_type:
        chatgpt_conf = chat_conf['openai-chatgpt']
        user_models[uid] = ChatGPT(
            uid=uid,
            api_key=display(chatgpt_conf['api-key']),
            max_req_length=display(chatgpt_conf['max-req-length']),
            max_resp_tokens=display(chatgpt_conf['max-resp-tokens']),
            proxy=display(chatgpt_conf['proxy']),
            from_type=from_type,
            need_ctx=need_ctx,
            model_id=model_id)
    elif 'openai'==chat_type or 'openai' in chat_type:
        openai_conf = chat_conf['openai']
        user_models[uid] = OpenAI(
            uid=uid,
            api_key=display(openai_conf['api-key']),
            max_req_length=display(openai_conf['max-req-length']),
            max_resp_tokens=display(openai_conf['max-resp-tokens']),
            proxy=display(openai_conf['proxy']),
            from_type=from_type,
            need_ctx=need_ctx,
            model_id=model_id)
    else:
        return f"未找到 {chat_type}"


def u_model(uid, from_type=None, need_ctx=True, need_ins=True) -> ChatAI:
    if not user_models.get(uid):
        u_change_model(uid, 'openai-chatgpt', from_type, need_ctx, need_ins)
    return user_models.get(uid)


def chat(uid: str, query: str, from_type: str):
    query = query.strip()
    if query[0] == "画":
        return aiimage.draw(uid, query[1:], from_type)
    if query.find("#changechat") == 0:
        chat_type = query.replace("#changechat", "", 1).strip()
        err = u_change_model(uid, chat_type, from_type)
        return err or f"#changechat {chat_type}"
    elif query.find("#changeimage") == 0:
        image_type = query.replace("#changeimage", "", 1).strip()
        err = aiimage.u_change_model(uid, image_type, from_type)
        return err or f"#changeimage {image_type}"
    reply, err = u_model(uid, from_type).reply(query)
    return err or reply


__all__ = [
    "chat",
    "u_model",
    "ChatAI",
    "OpenAI",
]
