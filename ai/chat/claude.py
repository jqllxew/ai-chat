import base64
import io

from anthropic._types import NOT_GIVEN

from ai.base import ClaudeClient
from ai.chat.gpt import ChatGPT
from config import match_image, match, custom_token_len
from logger import logger


class ChatClaude(ChatGPT):

    def __init__(self, model_id="claude-3-7-sonnet-20250219-r", **kw):
        _client = ClaudeClient()
        super().__init__(model_id, model_select=_client.model_select, **kw)
        self._client = _client
        self.system_text = None

    def _stream(self, prompt, token_len):
        with self._client.client.messages.stream(
                model=self.model_id,
                max_tokens=token_len if token_len is not None else self.max_resp_tokens,
                temperature=0.8,
                system=self.system_text or NOT_GIVEN,
                messages=prompt
        ) as _st:
            for x in _st.text_stream:
                yield x

    def _create(self, prompt, token_len):
        message = self._client.client.messages.create(
            model=self.model_id,
            max_tokens=token_len if token_len is not None else self.max_resp_tokens,
            temperature=0.8,
            system=self.system_text or NOT_GIVEN,
            messages=prompt
        )
        print(message)
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
