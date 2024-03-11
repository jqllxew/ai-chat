import threading
from typing import Callable

from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

import journal
from aichat.gpt import ChatGPT

tokenizer = None
model = None


class Yi6b(ChatGPT):
    def __init__(self, model_id, max_tokens, max_resp_tokens, **kw):
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

    def generate(self, query: str, jl: journal.Journal, stream=False):
        prompt = self.get_prompt(query)
        jl.prompt_len = self.get_prompt_len(prompt)
        jl.before(query, prompt)
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
                "max_new_tokens": self.max_resp_tokens,
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
