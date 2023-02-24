
from abc import ABC, abstractmethod
from collections import deque

import aiimage

# 用户上下文存储 K=uid,V=deque
user_contexts: dict[str, deque] = {}


class ChatAI(ABC):

    def __init__(self, uid: str, need_ctx=True):
        self.need_ctx = need_ctx
        self.uid = uid

    def get_prompt(self, query="", sep="\r\n") -> str:
        """
        :param query: 用户发来的文本消息
        :param sep: 分隔符
        :return: 上下文
        """
        if user_contexts.get(self.uid) is None:
            user_contexts[self.uid] = deque()
        if query:
            user_contexts[self.uid].append(query)
        return sep.join(user_contexts[self.uid])

    @abstractmethod
    def generate(self, prompt: str, stream=False):
        """
        :param prompt:
        :param stream:
        :return: text:str or Iterator[str]
        """
        raise NotImplementedError

    def reply(self, query: str, stream=False, before=None, after=None, error=None):
        """
        :param query: 用户发来的文本消息
        :param stream: 是否返回生成器
        :param before:
        :param after:
        :param error:
        :return: reply content
        """
        ins = self.instruction(query, self.uid)
        if ins:
            yield ins
        if self.need_ctx:
            prompt = self.get_prompt(query)
        else:
            prompt = query
        try:
            if callable(before):
                before(self.uid, query, prompt)
            res = self.generate(prompt, stream)
            if stream:
                res_text = ""
                for x in res:
                    yield x
                    res_text += x
            else:
                res_text = res
            res_text = res_text.strip()
            if self.need_ctx:
                user_contexts[self.uid].append(res_text)
            if callable(after):
                after(self.uid, res_text)
            if not stream:
                yield res_text
        except Exception as e:
            if callable(error):
                yield error(self.uid, e)
            else:
                yield e

    def reply_text(self, query: str, before=None, after=None, error=None):
        return next(self.reply(query, False, before, after, error))

    def reply_stream(self, query: str, before=None, after=None, error=None):
        return (x for x in self.reply(query, True, before, after, error))

    def reply_image(self, query: str, from_type: str) -> str:
        """
        :param query: 用户发来的绘画要求
        :param from_type: 消息来源
        :return: reply image_path
        """
        image_res = aiimage.generate(self.uid, query, from_type)
        reply_format = "提示词：{}\n负提示：{}\n随机数：{}\n耗时秒：{:.3f}\n宽高：{}\n".format(
            image_res.prompt if image_res.image is None else (image_res.prompt + '+[图片参数]'),
            "默认" if image_res.neg_prompt == "" else image_res.neg_prompt,
            image_res.seed, image_res.generate_seconds, f"{image_res.width}x{image_res.height}")
        if image_res.generate_err is None:
            if from_type == 'qq':
                reply_format += f"[CQ:image,file={image_res.generate_image_path}]"
            elif from_type == 'wx':
                reply_format += f"[image={image_res.generate_image_path}]"
            else:
                reply_format += image_res.generate_image_path
        else:
            reply_format += f"generate error because {image_res.generate_err}"
        return reply_format

    def instruction(self, query, _help=None):
        if query[0] == "#":
            if query == "#help":
                if callable(_help):
                    return _help()
                return "欢迎使用\n目前有以下指令可供使用：" \
                       "\n[#清空]清空您的会话记录" \
                       "\n[#长度]统计您的会话轮数与总字符长度" \
                       "\n[#add]添加会话记录上下文" \
                       "\n[#del]删除会话记录上下文（可加入条数#del x，表示删除最近x条）"
            elif "#add" in query:
                if user_contexts.get(self.uid) is None:
                    user_contexts[self.uid] = deque()
                ctx = user_contexts[self.uid]
                add_ctx = query.replace("#add", "", 1).strip()
                ctx.append(add_ctx)
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(ctx), len("\r\n".join(ctx)))
            elif query == "#ctx":
                with open("./models/default_ctx.txt", 'r', encoding='utf-8') as f:
                    if user_contexts.get(self.uid) is None:
                        user_contexts[self.uid] = deque()
                    lines = f.readlines()
                    for line in lines:
                        line = line.replace("\n", "", -1)
                        user_contexts[self.uid].append(line)
                    return "设置成功"
            elif user_contexts.get(self.uid) is not None:
                if query == "#清空":
                    user_contexts.pop(self.uid)
                    return f"[{self.uid}]的会话已清空，请继续新话题~"
                elif query == "#长度":
                    ctx = user_contexts[self.uid]
                    return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                        .format(self.uid, len(ctx), len("\r\n".join(ctx)))
                elif "#del" in query:
                    ctx = user_contexts[self.uid]
                    num = query.replace("#del", "", 1).strip()
                    if num == "":
                        num = 1
                    else:
                        num = int(num)
                    for i in range(num):
                        ctx.pop()
                    return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                        .format(self.uid, len(ctx), len("\r\n".join(ctx)))
            else:
                return "你还未产生对话数据！"
        return None
