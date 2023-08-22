import aiimage
from config import chat as chat_conf, display
from .chatai import ChatAI
from .gpt import OpenAI, ChatGPT
from .spark import ChatSpark

user_models: dict[str, ChatAI] = {}


def u_change_model(uid, chat_type='', from_type=None, enable_ctx=True, enable_ins=True, model_id=None) -> str:
    if 'gpt' == chat_type or 'chatgpt' == chat_type:
        if not isinstance(user_models.get(uid), ChatGPT):
            gpt_conf = chat_conf['openai']['gpt']
            user_models[uid] = ChatGPT(
                uid=uid,
                api_key=display(gpt_conf['api-key']),
                proxy=display(gpt_conf['proxy']),
                default_system=display(gpt_conf['default-system']),
                from_type=from_type,
                model_id=model_id,
                enable_ctx=enable_ctx,
                enable_ins=enable_ins)
    elif 'glm' == chat_type:
        from .glm import ChatGLM
        if not isinstance(user_models.get(uid), ChatGLM):
            glm_conf = chat_conf['thudm']['glm']
            user_models[uid] = ChatGLM(
                uid=uid,
                from_type=from_type,
                enable_ctx=enable_ctx,
                model_id=glm_conf['model-id'],
                max_length=glm_conf['max-length'],
                top_p=glm_conf['top-p'],
                temperature=glm_conf['temperature'],
                quantize=glm_conf['quantize'],
            )
    elif 'spark' == chat_type:
        if not isinstance(user_models.get(uid), ChatSpark):
            spark_conf = chat_conf['iflytek']['spark']
            user_models[uid] = ChatSpark(
                uid=uid,
                from_type=from_type,
                enable_ctx=enable_ctx,
                model_id=spark_conf['model-id'],
                app_id=spark_conf['app-id'],
                api_secret=spark_conf['api-secret'],  # 填写控制台中获取的 APISecret 信息
                api_key=spark_conf['api-key'],  # 填写控制台中获取的 APIKey 信息
            )
    else:
        return f"未找到 {chat_type}"


def u_model(uid, from_type=None, enable_ctx=True, enable_ins=True) -> ChatAI:
    if not user_models.get(uid):
        u_change_model(uid, 'gpt', from_type, enable_ctx, enable_ins)
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
