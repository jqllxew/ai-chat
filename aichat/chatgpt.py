import openai
from .open_ai import OpenAI


class ChatGPT(OpenAI):

    def __init__(self, api_key, max_req_length, max_resp_tokens, model_id=None, **kw):
        super().__init__(api_key, max_req_length, max_resp_tokens, **kw)
        self.model_id = model_id or "gpt-3.5-turbo"

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        reply and self.ctx.append({"role": "assistant", "content": reply})

    def join_ctx(self, sep=...):
        return self.ctx

    def get_prompt_len(self, prompt):
        return sum((len(x.get('content') or '') for x in self.ctx if x))

    def generate(self, prompt, stream=False):
        res = openai.ChatCompletion.create(
            model=self.model_id,
            max_tokens=self.max_resp_tokens,
            messages=prompt,
            stream=stream)
        if stream:
            return (x.choices[0]['delta'].get('content') or '' for x in res)
        return res.choices[0]['message'].get('content')

    def instruction(self, query, chat_type='openai-chatgpt'):
        return super().instruction(query, chat_type)
