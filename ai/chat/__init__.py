from config import chat as chat_conf, display
from .chatai import ChatAI
from .claude import ChatClaude
from .deepseek import DeepSeekApi, DeepSeekLocal
from .gpt import ChatGPT
from .spark import ChatSpark
from .yi6b import Yi6b

user_models: dict[str, ChatAI] = {}


def u_change_model(uid, chat_type='', from_type=None, enable_ctx=True, enable_ins=True) -> str:
    if 'gpt' == chat_type or 'chatgpt' == chat_type:
        if type(user_models.get(uid)) is not ChatGPT:
            user_models[uid] = ChatGPT(
                uid=uid,
                model_id=display(chat_conf['openai']['gpt']['default']),
                default_system=display(chat_conf['openai']['gpt']['default-system']),
                from_type=from_type,
                enable_ctx=enable_ctx,
                enable_ins=enable_ins
            )
    elif 'claude' == chat_type:
        if type(user_models.get(uid)) is not ChatClaude:
            user_models[uid] = ChatClaude(
                uid=uid,
                default_system=display(chat_conf['anthropic']['claude']['default-system']),
                from_type=from_type,
                enable_ctx=enable_ctx,
                enable_ins=enable_ins
            )
    elif 'glm' == chat_type:
        from .glm import ChatGLM
        if type(user_models.get(uid)) is not ChatGLM:
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
        if type(user_models.get(uid)) is not ChatSpark:
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
    elif 'yi' == chat_type:
        if type(user_models.get(uid)) is not Yi6b:
            yi_conf = chat_conf['yi']['yi-6b-chat']
            user_models[uid] = Yi6b(
                uid=uid,
                from_type=from_type,
                enable_ctx=enable_ctx,
                model_id=yi_conf['model-id'],
                max_tokens=yi_conf['max-tokens'],
                max_resp_tokens=yi_conf['max-resp-tokens']
            )
    elif 'deepseek' == chat_type:
        if type(user_models.get(uid)) is not DeepSeekApi:
            user_models[uid] = DeepSeekApi(
                uid=uid,
                default_system=display(chat_conf['deepseek']['api']['default-system']),
                from_type=from_type,
                enable_ctx=enable_ctx,
                enable_ins=enable_ins
            )
    elif 'deepseek-local' == chat_type:
        if type(user_models.get(uid)) is not DeepSeekLocal:
            user_models[uid] = DeepSeekLocal(
                uid=uid,
                model_id=display(chat_conf['deepseek']['local']['model-id']),
                default_system=display(chat_conf['deepseek']['local']['default-system']),
                from_type=from_type,
                enable_ctx=enable_ctx,
                enable_ins=enable_ins,
                max_tokens=chat_conf['deepseek']['local']['max-tokens'],
                max_resp_tokens=chat_conf['deepseek']['local']['max-resp-tokens']
            )
    else:
        return f"未找到 {chat_type}"


def u_model(uid, from_type=None, enable_ctx=True, enable_ins=True) -> ChatAI:
    if not user_models.get(uid):
        u_change_model(uid, chat_conf['default'], from_type, enable_ctx, enable_ins)
    return user_models.get(uid)


__all__ = [
    "u_model",
    "u_change_model",
    "ChatAI",
    "ChatClaude",
    "ChatGPT",
    "ChatSpark",
    "Yi6b",
    "DeepSeekApi"
]
