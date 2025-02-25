from typing import Callable

from openai import OpenAI

from aichat.gpt import ChatGPT
from config import chat as chat_conf, display

_model_select = display(chat_conf['deepseek']['api']['model-select'])
_api_key = display(chat_conf['deepseek']['api']['api-key'])
if _api_key:
    client = OpenAI(api_key=_api_key, base_url="https://api.deepseek.com")


class DeepSeekApi(ChatGPT):

    def __init__(self, model_id="deepseek-reasoner", default_system=None, **kw):
        super().__init__(model_id=model_id, default_system=default_system, model_select=_model_select, **kw)

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
