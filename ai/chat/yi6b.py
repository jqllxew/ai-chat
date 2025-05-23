from typing import Callable
from ai.chat.gpt import ChatGPT

tokenizer = None
model = None


class Yi6b(ChatGPT):

    def __init__(self, model_id, max_tokens, max_resp_tokens, **kw):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        super().__init__(**kw)
        self.model_id = model_id or "01-ai/Yi-6b-Chat"
        global tokenizer, model
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=False)
        if model is None:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id, device_map="auto", torch_dtype='auto',  # num_beams=1
            ).eval()
        self.max_tokens = max_tokens
        self.max_resp_tokens = max_resp_tokens
        self.max_req_tokens = max_tokens - max_resp_tokens

    def encode_len(self) -> Callable[[str], int]:
        def tokenize(value: str) -> int:
            return len(tokenizer.tokenize(value))

        return tokenize

    def generate(self, query: str, stream=False):
        return super().transformers_generate(tokenizer, model, query, stream)
