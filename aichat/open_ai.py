import openai

from config import chat as chat_conf, display
from logger import logger
from .chat_ai import ChatAI


class OpenAI(ChatAI):
    def __init__(self, api_key: str, max_req_length: int, max_resp_tokens: int, **kwargs):
        super().__init__(**kwargs)
        openai.api_key = api_key
        if self.model_id is None:
            self.model_id = "text-davinci-003"
        self.max_req_length = max_req_length
        self.max_resp_tokens = max_resp_tokens

    # overwrite
    def get_prompt(self, query="", sep="\n\n"):
        prompt = super().get_prompt(query, sep)
        while len(prompt) > self.max_req_length:
            logger.warn(f"[OPEN_AI] {self.uid}:ctx_word_count {len(prompt)} > {self.max_req_length}")
            self.ctx.popleft()
            prompt = super().get_prompt(sep=sep)
        return prompt

    def generate(self, prompt: str, stream=False):
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
        else:
            return res.choices[0].text

    def reply_text(self, query: str, stream=False, _before=None, _after=None, _error=None):
        return super().reply_text(
            query=query, stream=stream,
            _before=lambda _, x: f"[OPEN_AI]{self.uid}-len:{len(x)}\n{x}",
            _after=lambda x: f"[OPEN_AI]{self.uid}-reply:{x}",
            _error=lambda x: f"[OPEN_AI]{self.uid}-error:{x}"
        )

    def instruction(self, query, _help=None):
        ins = super().instruction(query)
        if ins is None and "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            model_select = display(chat_conf['openai']['model-select'])
            if model_select is not None and model_id in model_select:
                self.model_id = model_id
                ins = f"[{self.uid}]已切换模型{model_id}"
            else:
                ins = f"未找到{model_id}"
        return ins
