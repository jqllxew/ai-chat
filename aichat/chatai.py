import traceback
from abc import ABC, abstractmethod

import journal
from ai import ReplyAI


class ChatAI(ReplyAI, ABC):

    def __init__(self, need_ctx=True, need_ins=True, **kw):
        super().__init__(**kw)
        self.need_ctx = need_ctx
        self.need_ins = need_ins
        self.ctx = list()

    def join_ctx(self, sep="\r\n"):
        return sep.join(self.ctx)

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append(query)
        reply and self.ctx.append(reply)

    def get_prompt(self, query=""):
        """
        :param query: 用户发来的文本消息
        :return: prompts
        """
        if self.need_ctx:
            self.append_ctx(query)
            return self.join_ctx()
        return query

    def get_prompt_len(self, prompt):
        return len(prompt)

    @abstractmethod
    def generate(self, prompt, stream=False):
        """
        :param prompt:
        :param stream:
        :return: text:str or Iterator[str]
        """
        raise NotImplementedError

    def reply_text(self, query: str, stream=False, jl: journal.Journal = None):
        """
        :param jl: journal环绕调用
        :param query: 用户发来的文本消息
        :param stream: 是否返回生成器
        :return: reply content
        """
        ins = self.instruction(query) if self.need_ins else None
        if ins:
            yield ins
        else:
            prompt = self.get_prompt(query)
            if not jl:
                jl = journal.default_journal(**self.__dict__)
            jl.prompt_len = self.get_prompt_len(prompt)
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
                    self.append_ctx(reply=res_text)
                jl.after(res_text)
                if not stream:
                    yield res_text
            except Exception as e:
                jl.error(e)
                raise e

    def reply(self, query: str, jl=None) -> (str, str):
        try:
            return next(self.reply_text(query, False, jl)), None
        except Exception as e:
            traceback.print_exc()
            return None, f"err: {e}"

    def reply_stream(self, query: str, jl=None):
        return (x for x in self.reply_text(query, True, jl))

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
                self.append_ctx(add_ctx)
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
            elif query == "#ctx":
                with open("./models/default_ctx.txt", 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        line = line.replace("\n", "", -1)
                        self.append_ctx(query=line) if i % 2 == 0 else self.append_ctx(reply=line)
                    return "设置成功"
            elif query == "#清空":
                self.ctx = list()
                return f"[{self.uid}]的会话已清空，请继续新话题~"
            elif query == "#长度":
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
            elif "#del" in query:
                num = query.replace("#del", "", 1).strip()
                if num == "":
                    num = 1
                else:
                    num = int(num)
                for i in range(num):
                    self.ctx.pop()
                return "[{}]会话信息如下：\n总轮数为{}\n总字符长度为{}" \
                    .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
        return None
