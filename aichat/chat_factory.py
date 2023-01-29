
from collections import deque

from config import chat as chat_conf, display
from aichat.chat import user_model_id, user_contexts, ChatAI
from aichat.open_ai import OpenAI

chat_models: dict[str, ChatAI] = {}


def chat(uid: int, query: str, from_type: str):
    query = query.strip()
    cmd_res = command(query, uid)
    if cmd_res is not None:
        return cmd_res
    openai_conf = display(chat_conf['openai'])
    if openai_conf is not None:
        model_id = user_model_id.get(uid)
        if model_id is None:
            model_id = openai_conf['model-select'][0]
        if chat_models.get(model_id) is None:
            chat_models[model_id] = OpenAI(
                api_key=openai_conf['api-key'],
                model_id=model_id,
                max_req_length=openai_conf['max-req-length'],
                max_resp_tokens=openai_conf['max-resp-tokens']
            )
        if query[0] == "画":
            _query = query[1:]
            return chat_models[model_id].reply_image(uid, _query, from_type)
        return chat_models[model_id].reply_text(uid, query)
    return ""


def command(query, uid):
    if uid is None or query[0] != "#":
        return None
    if query == "#help":
        return "欢迎使用\n目前有以下指令可供使用：" \
               "\n[#清空]清空您的会话记录" \
               "\n[#长度]统计您的会话轮数与总字符长度" \
               "\n[#add]添加会话记录上下文" \
               "\n[#del]删除会话记录上下文（可加入条数#del x，表示删除最近x条）"
    elif "#切换" in query:
        model_id = query.replace("#切换", "", 1).strip()
        model_select = display(chat_conf['openai']['model-select'])
        if model_select is not None and model_id in model_select:
            user_model_id[uid] = model_id
            if user_contexts.get(uid) is not None:
                user_contexts.pop(uid)
            return f"[用户{uid}]已切换模型为{model_id}"
        return f"未找到{model_id}"
    elif "#add" in query:
        if user_contexts.get(uid) is None:
            user_contexts[uid] = deque()
        ctx = user_contexts[uid]
        add_ctx = query.replace("#add", "", 1).strip()
        ctx.append(add_ctx)
        return "[用户{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
            .format(uid, len(ctx), len("\r\n".join(ctx)))
    elif query == "#ctx":
        with open("./models/default_ctx.txt", 'r', encoding='utf-8') as f:
            if user_contexts.get(uid) is None:
                user_contexts[uid] = deque()
            lines = f.readlines()
            for line in lines:
                line = line.replace("\n", "", -1)
                user_contexts[uid].append(line)
            return "设置成功"
    elif user_contexts.get(uid) is not None:
        if query == "#清空":
            user_contexts.pop(uid)
            return f"[用户{uid}]的会话已清空，请继续新话题~"
        elif query == "#长度":
            ctx = user_contexts[uid]
            return "[用户{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                .format(uid, len(ctx), len("\r\n".join(ctx)))
        elif "#del" in query:
            ctx = user_contexts[uid]
            num = query.replace("#del", "", 1).strip()
            if num == "":
                num = 1
            else:
                num = int(num)
            for i in range(num):
                ctx.pop()
            return "[用户{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                .format(uid, len(ctx), len("\r\n".join(ctx)))
    else:
        return "你还未产生对话数据！"
    return None
