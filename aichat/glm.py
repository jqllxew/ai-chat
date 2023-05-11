import torch
from transformers import AutoTokenizer, AutoModel

from logger import logger
from .chatai import ChatAI

model = None
tokenizer = None


class ChatGLM(ChatAI):
    def __init__(self, model_id=None, max_length=2048, top_p=0.7, temperature=0.95, quantize=..., **kw):
        super().__init__(**kw)
        self.model_id = model_id or 'THUDM/chatglm-6b'
        self.max_length = max_length
        self.top_p = top_p
        self.temperature = temperature
        self.quantize = quantize if isinstance(quantize, int) else None
        global model, tokenizer
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        if model is None:
            if self.quantize:
                model = AutoModel.from_pretrained(self.model_id, trust_remote_code=True) \
                    .quantize(self.quantize).half().cuda()
            else:
                model = AutoModel.from_pretrained(self.model_id, trust_remote_code=True).half().cuda()
            model = model.eval()

    def append_ctx(self, query=None, reply=None):
        if query:
            self.ctx.append([query])
        if reply:
            for x in self.ctx:
                if isinstance(x, list) and len(x) == 1:
                    x.append(reply)

    def get_prompt_len(self, prompt):
        total_word_count = 0
        for x in prompt:
            for msg in x:
                total_word_count += len(msg)
        return total_word_count

    def get_prompt(self, query=""):
        self.append_ctx(query)
        prompt = self.join_ctx()
        while self.get_prompt_len(prompt) > self.max_length:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(prompt)} > {self.max_length}")
            if len(self.ctx) > 1:
                self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")
            prompt = self.join_ctx()
        return prompt

    def generate(self, prompt, stream=False):
        global model, tokenizer
        history = []
        query = prompt[-1][0]
        for x in prompt[:-1]:
            if isinstance(x, list) and len(x) == 2:
                history.append((x[0], x[1]))
        try:
            if stream:
                return (x for x, _ in model.stream_chat(
                    tokenizer, query,
                    history=history,
                    max_length=self.max_length,
                    top_p=self.top_p,
                    temperature=self.temperature
                ))
            res, _ = model.chat(tokenizer, query,
                                history=history,
                                max_length=self.max_length,
                                top_p=self.top_p,
                                temperature=self.temperature)
            return res
        finally:
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
