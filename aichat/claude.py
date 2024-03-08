import anthropic
from anthropic._types import NOT_GIVEN
from anthropic.types import ContentBlock
import journal
from aichat.gpt import ChatGPT
from config import chat as chat_conf, display

_model_select = display(chat_conf['anthropic']['claude']['model-select'])
_api_key = display(chat_conf['anthropic']['claude']['api-key'])
_api_proxy = display(chat_conf['anthropic']['claude']['proxy'])

if _api_key:
    client = anthropic.Anthropic(
        api_key=_api_key,
        proxies=_api_proxy
    )


class ChatClaude(ChatGPT):

    def __init__(self, model_id="claude-3-sonnet-20240229", **kw):
        super().__init__(model_id, model_select=_model_select, **kw)
        self.system_text = None
        self._model_select = _model_select

    def _stream(self, prompt):
        with client.messages.stream(
                model=self.model_id,
                max_tokens=self.max_resp_tokens,
                temperature=0.8,
                system=self.system_text or NOT_GIVEN,
                messages=prompt
        ) as _st:
            for x in _st.text_stream:
                yield x

    def _create(self, prompt):
        message = client.messages.create(
            model=self.model_id,
            max_tokens=self.max_resp_tokens,
            temperature=0.8,
            system=self.system_text or NOT_GIVEN,
            messages=prompt
        )
        if len(message.content) and isinstance(message.content[0], ContentBlock):
            return message.content[0].text

    def generate(self, query: str, jl: journal.Journal, stream=False):
        prompt = self.get_prompt(query)
        jl.prompt_len = self.get_prompt_len(prompt)
        jl.before(query, prompt)
        if stream:
            return self._stream(prompt)
        return self._create(prompt)

    def set_system(self, text):
        self.system_text = text

    def instruction(self, query):
        if "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            try:
                if model_id == "opus":
                    model_id = "claude-3-opus-20240229"
                elif model_id == "sonnet":
                    model_id = "claude-3-sonnet-20240229"
                self.set_model_attr(model_id)
                return f"[{self.uid}]已切换模型{model_id}"
            except Exception as e:
                return str(e)
        return super().instruction(query)