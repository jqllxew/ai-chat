from typing import Callable

from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk

from aichat.gpt import ChatGPT
from config import chat as chat_conf, display

_model_select = display(chat_conf['deepseek']['api']['model-select'])
_api_key = display(chat_conf['deepseek']['api']['api-key'])
if _api_key:
    client = OpenAI(api_key=_api_key, base_url="https://api.deepseek.com")


def _stream(response: Stream[ChatCompletionChunk]):
    flag = 0
    for chunk in response:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
            if flag == 0:
                flag = 1
                yield "<think>"
            yield delta.reasoning_content or ''
        else:
            if flag == 1:
                flag = 2
                yield "</think>"
            yield delta.content or ''


class DeepSeekApi(ChatGPT):

    def __init__(self, model_id="deepseek-reasoner", default_system=None, **kw):
        super().__init__(model_id=model_id, default_system=default_system, model_select=_model_select, **kw)

    def generate(self, query, stream=False):
        prompt, token_len = self.get_prompt(query)
        res = self.getClient().chat.completions.create(
            model=self.model_id,
            max_tokens=token_len if token_len is not None else self.max_resp_tokens,
            messages=prompt,
            stream=stream,
            n=1,  # 默认为1,对一个提问生成多少个回答
            temperature=1.2,  # 默认为1,0~2
        )
        if stream:
            return _stream(res)
        return res.choices[0].message.content

    def getClient(self):
        return client


tokenizer = None
model = None


class DeepSeekLocal(ChatGPT):

    def __init__(self, model_id, max_tokens, max_resp_tokens, default_system=None, **kw):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        super().__init__(model_id=model_id, default_system=default_system, model_select=_model_select, **kw)
        self.model_id = model_id
        global model, tokenizer
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        if model is None:
            model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True).half().cuda().eval()
        self.max_tokens = max_tokens
        self.max_resp_tokens = max_resp_tokens
        self.max_req_tokens = max_tokens - max_resp_tokens

    def encode_len(self) -> Callable[[str], int]:
        def tokenize(value: str) -> int:
            return len(tokenizer.tokenize(value))

        return tokenize

    def generate(self, query: str, stream=False):
        return super().transformers_generate(tokenizer, model, query, stream)

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        if reply:
            think = "</think>"
            index = reply.find(think)
            if index != -1:
                reply = reply[index + len(think):]
            self.ctx.append({"role": "assistant", "content": reply})
