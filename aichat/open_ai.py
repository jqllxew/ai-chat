import openai
from config import chat as chat_conf, display
from .chat import ChatAI, user_contexts


class OpenAI(ChatAI):
    def __init__(self, api_key: str, uid: str, max_req_length: int, max_resp_tokens: int, model_id="", need_ctx=True):
        super().__init__(uid, need_ctx)
        openai.api_key = api_key
        self.model_id = model_id if model_id else "text-davinci-003"
        self.max_req_length = max_req_length
        self.max_resp_tokens = max_resp_tokens

    # overwrite
    def get_prompt(self, query="", sep="\n\n"):
        prompt = super().get_prompt(query, sep)
        while len(prompt) > self.max_req_length:
            print(f"[OPEN_AI]上下文长度 {len(prompt)} 超过 {self.max_req_length}")
            user_contexts[self.uid].popleft()
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

    def reply(self, query: str, stream=False, before=None, after=None, error=None):
        def _before(prompt: str):
            print(f"[OPEN_AI] len {len(prompt)}\n{prompt}")
            if callable(before):
                before(prompt)

        def _after(reply: str):
            print(f"[OPEN_AI] reply={reply}")
            if callable(after):
                after(reply)

        def _error(e: Exception):
            errmsg = f"[OPEN_AI]错误信息: {e}"
            print(errmsg)
            if self.need_ctx:
                user_contexts[self.uid].pop()
            if callable(error):
                error(e)
            return errmsg
        return super().reply(query, stream, _before, _after, _error)

    def reply_image(self, query: str, from_type: str):
        return super().reply_image(query, from_type)

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
