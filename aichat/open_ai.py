import openai

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

    # overwrite
    def get_prompt(self, query=""):
        prompt = super().get_prompt(query)
        while self.get_prompt_len(prompt) > self.max_req_length:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(prompt)} > {self.max_req_length}")
            self.ctx.pop(0)
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
            frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            presence_penalty=0.6,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            stop=["#"],
            stream=stream)
        if stream:
            return (x.choices[0].text for x in res)
        return res.choices[0].text

    def reply_text(self, query: str, stream=False, before=None, after=None, error=None):
        return super().reply_text(
            query=query, stream=stream,
            before=before or (lambda _, x: logger.info(f"[{self.model_id}]{self.uid}-len:{len(x)}\n{x}")),
            after=after or (lambda x, _: logger.info(f"[{self.model_id}]{self.uid}-reply:{x}")),
            error=error or (lambda x, _: logger.warn(f"[{self.model_id}]{self.uid}-error:{x}"))
        )

    def instruction(self, query, chat_type='openai'):
        if "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            model_select = display(chat_conf[chat_type]['model-select'])
            if model_select and model_id in model_select:
                self.model_id = model_id
                return f"[{self.uid}]已切换模型{model_id}"
            return f"未找到{model_id}"
        return super().instruction(query)
