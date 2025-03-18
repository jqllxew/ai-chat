import threading
import traceback
from abc import ABC, abstractmethod
from typing import Callable

from bs4 import BeautifulSoup
import journal
import tiktoken
from ai.base import ReplyAI


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

    def get_prompt(self, query="") -> (str, int):
        """
        :param query: 用户发来的文本消息
        :return: prompts
        """
        if self.enable_ctx:
            self.append_ctx(query)
            return self.join_ctx()
        return query, None

    def encode_len(self) -> Callable[[str], int]:
        try:
            encoding = tiktoken.encoding_for_model(self.model_id)
        except:
            encoding = tiktoken.get_encoding("cl100k_base")

        def tiktoken_encode(value) -> int:
            return len(encoding.encode(value))

        return tiktoken_encode

    def get_prompt_len(self, prompt):
        """Returns the number of tokens used by a list of messages."""
        encoder = self.encode_len()
        if not callable(encoder):
            raise RuntimeError("encode_len return is not function")

        def count_tokens(value):
            """Recursively count tokens in a value."""
            if isinstance(value, str):
                return encoder(value)
            elif isinstance(value, list):
                _num_tokens = 0
                for item in value:
                    _num_tokens += count_tokens(item)
                return _num_tokens
            elif isinstance(value, dict):
                if "type" in value and value["type"] == "base64":
                    return 0  # Ignore tokens for base64 content
                _num_tokens = 0
                for sub_value in value.values():
                    _num_tokens += count_tokens(sub_value)
                return _num_tokens
            else:
                # Handle other types, e.g., integers, floats, etc.
                return 1

        num_tokens = count_tokens(prompt)
        num_tokens += len(prompt) * 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        if num_tokens > 0:
            num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    @abstractmethod
    def generate(self, query: str, stream=False):
        """
        :param query:
        :param stream:
        :return: text:str or Iterator[str]
        """
        raise NotImplementedError

    @abstractmethod
    def set_system(self, system_text):
        raise NotImplementedError

    @journal.reply_log
    def reply_text(self, query: str, stream=False, _done=lambda x: x):
        """
        :param _done:
        :param query: 用户发来的文本消息
        :param stream: 是否返回生成器
        :return: reply content
        """
        ins = self.instruction(query) if self.enable_ins else None
        if ins:
            yield ins
        else:
            res = self.generate(query, stream)
            if stream:
                res_text = ""
                for x in res:
                    yield x
                    res_text += x
            else:
                res_text = res
            res_text = res_text.strip()
            _done(res_text)
            if self.enable_ctx:
                self.append_ctx(reply=res_text)
            if not stream:
                yield res_text

    def reply(self, query: str) -> (str, str):
        try:
            return next(self.reply_text(query, False)), None
        except Exception as e:
            traceback.print_exc()
            return None, f"err: {e}"

    def reply_stream(self, query: str):
        try:
            for x in self.reply_text(query, True):
                yield x
        except Exception as e:
            traceback.print_exc()
            yield f"err: {e}"

    def transformers_generate(self, tokenizer, model, query: str, stream=False):
        from transformers import TextIteratorStreamer
        prompt, token_len = self.get_prompt(query)
        input_ids = tokenizer.apply_chat_template(
            prompt,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors='pt'
        )
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        _thread = threading.Thread(
            target=model.generate,
            kwargs={
                "input_ids": input_ids.to('cuda'),
                "max_new_tokens": token_len if token_len is not None else self.max_resp_tokens,
                "streamer": streamer,
                "do_sample": True,
                "repetition_penalty": 1.3,
                "no_repeat_ngram_size": 5,
                "temperature": 0.7,
                "top_k": 40,
                "top_p": 0.8
            }
        )
        _thread.start()
        if stream:
            return streamer
        else:
            _thread.join()
            result = ''.join(streamer)
            return result

    def instruction(self, query):
        if query[0] == "#":
            if query == "#help":
                return "欢迎使用\n目前有以下指令可供使用：" \
                       "\n[#清空]清空您的会话记录" \
                       "\n[#len]统计您的会话轮数与总令牌数" \
                       "\n[#changechat]切换聊天ai（可选glm/gpt/spark/yi）" \
                       "\n[#changeimage]切换图像生成（可选diffusion/diffusers/dallE）" \
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
                self.set_system(None)
                self.ctx.clear()
                return f"[{self.uid}]的会话已清空，请继续新话题~"
            elif query == "#len":
                return "[{}]会话信息如下：\n当前模型{}\n总轮数为{}\n总令牌数为{}" \
                    .format(self.uid, self.model_id, len(self.ctx), self.get_prompt_len(self.join_ctx()))
            elif "#del" in query:
                num = query.replace("#del", "", 1).strip()
                if num == "":
                    num = 1
                else:
                    num = int(num)
                for i in range(num):
                    self.ctx.pop()
                return "[{}]会话信息如下：\n总轮数为{}\n总令牌数为{}" \
                    .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
        return None
