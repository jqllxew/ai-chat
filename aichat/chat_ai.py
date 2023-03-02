
from abc import ABC, abstractmethod
from collections import deque
import journal
from ai import ReplyAI


class ChatAI(ReplyAI, ABC):

    def __init__(self, need_ctx=True, **kwargs):
        super().__init__(**kwargs)
        self.need_ctx = need_ctx
        self.ctx = deque()

    def get_prompt(self, query="", sep="\r\n") -> str:
        """
        :param query: 用户发来的文本消息
        :param sep: 分隔符
        :return: 上下文
        """
        if query:
            self.ctx.append(query)
        return sep.join(self.ctx)

    @abstractmethod
    def generate(self, prompt: str, stream=False):
        """
        :param prompt:
        :param stream:
        :return: text:str or Iterator[str]
        """
        raise NotImplementedError

    def reply_text(self, query: str, stream=False, before=..., after=..., error=...):
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
        jl = journal.lifecycle(**self.__dict__,
                               _before=before, _after=after, _error=error)
        try:
            jl.before(query, prompt)
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
                self.ctx.append(res_text)
                jl.after(res_text)
            if not stream:
                yield res_text
        except Exception as e:
            yield jl.error(e)

    def reply(self, query: str, before=None, after=None, error=None):
        return next(self.reply_text(query, False, before, after, error))

    def reply_stream(self, query: str, before=None, after=None, error=None):
        return (x for x in self.reply_text(query, True, before, after, error))

    def instruction(self, query, _help=...):
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
                add_ctx = query.replace("#add", "", 1).strip()
                self.ctx.append(add_ctx)
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(self.ctx), len("\r\n".join(self.ctx)))
            elif query == "#ctx":
                with open("./models/default_ctx.txt", 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.replace("\n", "", -1)
                        self.ctx.append(line)
                    return "设置成功"
            elif query == "#清空":
                self.ctx = deque()
                return f"[{self.uid}]的会话已清空，请继续新话题~"
            elif query == "#长度":
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(self.ctx), len("\r\n".join(self.ctx)))
            elif "#del" in query:
                num = query.replace("#del", "", 1).strip()
                if num == "":
                    num = 1
                else:
                    num = int(num)
                for i in range(num):
                    self.ctx.pop()
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(self.ctx), len("\r\n".join(self.ctx)))
        return None
