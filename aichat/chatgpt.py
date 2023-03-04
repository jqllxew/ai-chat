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
            stream=stream,
            n=1,                        # 默认为1,对一个提问生成多少个回答
            temperature=1,              # 默认为1,0~2，数值越高创造性越强
            # top_p = 1,                # 默认为1,0~1，效果类似temperature，不建议都用
            # stop = '',                # 遇到stop停止生成内容
            # presence_penalty = 2,     # 默认为0,-2~2，越大越允许跑题
            # frequency_penalty = 1.8,  # 默认为0,-2~2，越大越不允许复读机
            # logit_bias = None,        # 默认无,影响特定词汇的生成概率？
            # user = 'test',            # 默认无,用户名
        )
        if stream:
            return (x.choices[0]['delta'].get('content') or '' for x in res)
        return res.choices[0]['message'].get('content')

    def instruction(self, query, chat_type='openai-chatgpt'):
        return super().instruction(query, chat_type)
