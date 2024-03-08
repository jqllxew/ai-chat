import traceback
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup
import journal
import tiktoken
from ai import ReplyAI


class ChatAI(ReplyAI, ABC):

    def __init__(self, enable_ctx=True, enable_ins=True, **kw):
        super().__init__(**kw)
        self.enable_ctx = enable_ctx
        self.enable_ins = enable_ins
        self.ctx = list()

    def join_ctx(self):
        return self.ctx

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append(query)
        reply and self.ctx.append(reply)

    def get_prompt(self, query=""):
        """
        :param query: 用户发来的文本消息
        :return: prompts
        """
        if self.enable_ctx:
            self.append_ctx(query)
            return self.join_ctx()
        return query

    def get_prompt_len(self, prompt):
        return len(prompt)

    @staticmethod
    def num_tokens_from_messages(messages, model = None) -> int:
        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model or "cl100k_base")
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                if not isinstance(value, str):
                    value = str(value)
                ss = encoding.encode(value)
                num_tokens += len(ss)
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        if num_tokens > 0:
            num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    @abstractmethod
    def generate(self, query: str, jl: journal.Journal, stream=False):
        """
        :param jl:
        :param query:
        :param stream:
        :return: text:str or Iterator[str]
        """
        raise NotImplementedError

    @abstractmethod
    def set_system(self, system_text):
        raise NotImplementedError

    def reply_text(self, query: str, stream=False, jl: journal.Journal = None):
        """
        :param jl: journal环绕调用
        :param query: 用户发来的文本消息
        :param stream: 是否返回生成器
        :return: reply content
        """
        ins = self.instruction(query) if self.enable_ins else None
        if ins:
            yield ins
        else:
            if not jl:
                jl = journal.default_journal(**self.__dict__)
            try:
                res = self.generate(query, jl, stream)
                if stream:
                    res_text = ""
                    for x in res:
                        yield x
                        res_text += x
                else:
                    res_text = res
                res_text = res_text.strip()
                if self.enable_ctx:
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
        return self.reply_text(query, True, jl)

    def instruction(self, query):
        if query[0] == "#":
            if query == "#help":
                return "欢迎使用\n目前有以下指令可供使用：" \
                       "\n[#清空]清空您的会话记录" \
                       "\n[#长度]统计您的会话轮数与总字符长度" \
                       "\n[#changechat]切换聊天ai（可选glm/gpt/spark/yi）" \
                       "\n[#changeimage]切换图像生成（可选diffusion/diffusers/dalle）" \
                       "\n[#draw]绘画指令" \
                       "\n[#ctx]导入聊天记录" \
                       "\n[#add]上下文中添加用户消息" \
                       "\n[#del]删除会话记录上下文（可加入条数#del x，表示删除最近x条）"
            elif "#add" in query:
                add_ctx = query.replace("#add", "", 1).strip()
                self.append_ctx(add_ctx)
                return "[{}]会话信息如下：\n总轮数为{}\n总字符(or tokens)长度为{}" \
                    .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
            elif "#ctx" in query:
                ctx_path = query.replace("#ctx", "", 1).strip()
                if not ctx_path:
                    ctx_path = "default_ctx.txt"
                with open(f"./models/{ctx_path}", 'r', encoding='utf-8') as f:
                    text = f.read()
                    soup = BeautifulSoup(text, 'html.parser')
                    for tag in soup.find_all():
                        tag_text = tag.get_text(strip=True)
                        if tag.name == "system":
                            self.set_system(tag_text)
                        elif tag.name == "user":
                            self.append_ctx(query=tag_text)
                        elif tag.name == "asst":
                            self.append_ctx(reply=tag_text)
                return "セットアップ完了"
            elif query == "#清空":
                self.ctx.clear()
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
