import base64
import io

import anthropic
from anthropic._types import NOT_GIVEN
from anthropic.types import ContentBlock
import journal
from aichat.gpt import ChatGPT
from config import chat as chat_conf, display, match_image, match, custom_token_len
from logger import logger

_model_select = display(chat_conf['anthropic']['claude']['model-select'])
_api_key = display(chat_conf['anthropic']['claude']['api-key'])
_api_proxy = display(chat_conf['anthropic']['claude']['proxy'])

if _api_key:
    client = anthropic.Anthropic(
        api_key=_api_key,
        proxies=_api_proxy
    )


class ChatClaude(ChatGPT):

    def __init__(self, model_id="claude-3-5-sonnet-20241022", **kw):
        super().__init__(model_id, model_select=_model_select, **kw)
        self.system_text = None
        self._model_select = _model_select

    def _stream(self, prompt, token_len):
        with client.messages.stream(
                model=self.model_id,
                max_tokens=token_len if token_len is not None else self.max_resp_tokens,
                temperature=0.8,
                system=self.system_text or NOT_GIVEN,
                messages=prompt
        ) as _st:
            for x in _st.text_stream:
                yield x

    def _create(self, prompt, token_len):
        message = client.messages.create(
            model=self.model_id,
            max_tokens=token_len if token_len is not None else self.max_resp_tokens,
            temperature=0.8,
            system=self.system_text or NOT_GIVEN,
            messages=prompt
        )
        if len(message.content):
            return message.content[0].text

    def get_prompt(self, query=""):
        images, query = match_image(query)
        token_len, query = match(custom_token_len, query)
        if len(images):
            buffered = io.BytesIO()
            images[0].save(buffered, format="JPEG")
            # 获得字节流的内容
            image_content = buffered.getvalue()
            base64_image = base64.b64encode(image_content).decode("utf-8")
            query = [{
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image
                }
            }, {
                "type": "text",
                "text": query or "看看这张图吧"
            }]
        self.append_ctx(query)
        while self.get_prompt_len(self.ctx) > self.max_req_tokens:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(self.ctx)} > {self.max_req_tokens}")
            if len(self.ctx) > 1:
                self.ctx.pop(0)
                self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")

        return self.ctx, int(token_len[0]) if token_len else None

    def generate(self, query: str, stream=False):
        prompt, token_len = self.get_prompt(query)
        if stream:
            return self._stream(prompt, token_len)
        return self._create(prompt, token_len)

    def set_system(self, text):
        self.system_text = text

    def instruction(self, query):
        if "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            try:
                if model_id == "opus":
                    model_id = "claude-3-5-opus-20241022"
                elif model_id == "sonnet":
                    model_id = "claude-3-5-sonnet-20241022"
                self.set_model_attr(model_id)
                return f"[{self.uid}]已切换模型{model_id}"
            except Exception as e:
                return str(e)
        return super().instruction(query)
