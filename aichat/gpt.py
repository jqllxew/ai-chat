import openai
from bs4 import BeautifulSoup

from config import chat as chat_conf, display
from logger import logger
from .chatai import ChatAI


class OpenAI(ChatAI):
    def __init__(self, api_key, max_req_length, max_resp_tokens, proxy=None, model_id=None, **kw):
        super().__init__(**kw)
        openai.api_key = api_key
        openai.proxy = {
            'http': proxy,
            'https': proxy
        } if proxy else None
        self.model_id = model_id or "text-davinci-003"
        self.max_req_length = max_req_length
        self.max_resp_tokens = max_resp_tokens

    def join_ctx(self, sep="\n\n"):
        return sep.join(self.ctx)

    def get_prompt(self, query=""):
        prompt = super().get_prompt(query)
        while self.get_prompt_len(prompt) > self.max_req_length:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(prompt)} > {self.max_req_length}")
            if len(self.ctx) > 1:
                self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")
            prompt = super().get_prompt()
        return prompt

    def generate(self, prompt, stream=False):
        res = openai.Completion.create(
            model=self.model_id,  # 对话模型的名称
            prompt=prompt,
            temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
            # 回复最大的tokens，用达芬奇003来说需满足 prompt_tokens + max_tokens <= 4000
            # 参考文档的MAX REQUEST https://beta.openai.com/docs/models/gpt-3
            max_tokens=self.max_resp_tokens,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.6,
            stop=["#"],
            stream=stream)
        if stream:
            return (x.choices[0].text for x in res)
        return res.choices[0].text

    def instruction(self, query, chat_type='gpt3'):
        if "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            model_select = display(chat_conf['openai'][chat_type]['model-select'])
            if model_select and model_id in model_select:
                self.model_id = model_id
                return f"[{self.uid}]已切换模型{model_id}"
            return f"未找到{model_id}"
        return super().instruction(query)


class ChatGPT(OpenAI):
    def __init__(self, api_key, max_req_length, max_resp_tokens, model_id=None, default_system=None, **kw):
        super().__init__(api_key, max_req_length, max_resp_tokens, **kw)
        self.model_id = model_id or "gpt-3.5-turbo-0613"
        if default_system:
            self.set_system(default_system)

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        reply and self.ctx.append({"role": "assistant", "content": reply})

    def join_ctx(self, sep=...):
        return self.ctx

    def get_prompt_len(self, prompt):
        return sum((len(x.get('content') or '') for x in self.ctx if x))

    def get_prompt(self, query=""):
        self.append_ctx(query)
        prompt = self.join_ctx()
        while self.get_prompt_len(prompt) > self.max_req_length:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(prompt)} > {self.max_req_length}")
            if len(self.ctx) > 1:
                if isinstance(self.ctx[0], dict) and self.ctx[0].get('role') == "system":
                    if len(self.ctx) == 2:
                        raise RuntimeError("prompt text too long")
                    self.ctx.pop(1)
                else:
                    self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")
            prompt = self.join_ctx()
        return prompt

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

    def set_system(self, text):
        self.ctx.insert(0, {"role": "system", "content": text})

    def instruction(self, query, chat_type='gpt'):
        if "#system" in query:
            system_text = query.replace("#system", "", 1).strip()
            self.set_system(system_text)
            return "设置成功"
        if "#ctx" in query:
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
        return super().instruction(query, chat_type)
