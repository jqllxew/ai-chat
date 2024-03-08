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

    def set_system(self, system_text):
        self.ctx.insert(0, {"role": "system", "content": system_text})

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        reply and self.ctx.append({"role": "assistant", "content": reply})

    def get_prompt_len(self, prompt):
        return sum(len(tokenizer.tokenize(x.get("content"))) for x in prompt)

    def get_prompt(self, query=""):
        self.append_ctx(query)
        prompt = self.join_ctx()
        while self.get_prompt_len(prompt) > self.max_length:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(prompt)} > {self.max_length}")
            if len(self.ctx) > 1:
                if isinstance(self.ctx[0], dict) and self.ctx[0].get('role') == "system":
                    if len(self.ctx) == 2:
                        raise RuntimeError("prompt text too long")
                    self.ctx.pop(1)
                else:
                    self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")
        return self.ctx

    def generate(self, query, jl, stream=False):
        global model, tokenizer
        history = [x for x in self.get_prompt()]
        prompt = self.get_prompt(query)
        jl.prompt_len = self.get_prompt_len(prompt)
        jl.before(query, prompt)
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

    def instruction(self, query):
        if "#system" in query:
            system_text = query.replace("#system", "", 1).strip()
            self.set_system(system_text)
            return "セットアップ完了"
        return super().instruction(query)
