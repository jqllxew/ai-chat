import hashlib
import json
import time
from io import BytesIO

from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall

import plugin
from config import match, match_reply, match_image, custom_token_len
from logger import logger
from plugin import tx_cos
from .chatai import ChatAI
from ..base import OpenAIClient


class ChatGPT(ChatAI):
    def __init__(self, model_id="gpt-4o-mini", default_system=None, model_select=None, **kw):
        super().__init__(model_id=model_id, **kw)
        self._client = None
        self.model_id = model_id
        self.max_req_tokens = None
        self.max_resp_tokens = None
        self._cache_len = {}
        self.enable_function = False
        self._model_select = model_select
        self.set_model_attr(model_id)
        self.set_system(default_system)

    def getClient(self):
        if self._client is None:
            self._client = OpenAIClient()
        return self._client.client

    def set_model_attr(self, model_id=None):
        model_select = self._model_select
        if not self._client:
            self.getClient()
        if model_select is None and hasattr(self._client, "model_select"):
            model_select = self._client.model_select
        max_tokens = 12384
        max_resp_tokens = 512
        if model_select:
            model_attrs = model_select.get(self.model_id)
            if model_attrs:
                max_tokens = model_attrs['max-tokens']
                max_resp_tokens = model_attrs['max-resp-tokens']
        self.model_id = model_id
        self.max_resp_tokens = max_resp_tokens
        self.max_req_tokens = max_tokens - max_resp_tokens
        return f"[{self.uid}]已切换模型{model_id}"

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        reply and self.ctx.append({"role": "assistant", "content": reply})

    def get_prompt_len(self, prompt):
        _hash = hashlib.md5(str(prompt).encode()).hexdigest()
        if self._cache_len.get('_hash') != _hash:
            self._cache_len['_hash'] = _hash
            self._cache_len['_len'] = super().get_prompt_len(prompt)
        return self._cache_len['_len']

    def get_prompt(self, query=""):
        query = match_reply(query)
        token_len, query = match(custom_token_len, query)
        images, query = match_image(query)
        if len(images):
            if query:
                url = tx_cos.upload(
                    f"{self.model_id}/{self.uid}/{int(time.time() * 1000)}.jpg",
                    images[0]
                )
                logger.info(f"[{self.model_id}] img_url: {url}")
                query = [{
                    "type": "text",
                    "text": query
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                }]
            else:
                return None, token_len
        self.append_ctx(query)
        while self.get_prompt_len(self.ctx) > self.max_req_tokens:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(self.ctx)} > {self.max_req_tokens}")
            if len(self.ctx) > 1:
                if isinstance(self.ctx[0], dict) and self.ctx[0].get('role') == "system":
                    if len(self.ctx) == 2:
                        raise RuntimeError("prompt text too long")
                    self.ctx.pop(1)
                else:
                    self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")
        return self.ctx, int(token_len[0]) if token_len else None

    def generate(self, query, stream=False):
        client = self.getClient()
        prompt, token_len = self.get_prompt(query)
        if not prompt:
            return None
        if self.enable_function:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=prompt,
                tools=plugin.tools,
                tool_choice="auto"
            )
            response_message: ChatCompletionMessage = response.choices[0].message
            tool_calls: list[ChatCompletionMessageToolCall] = response_message.tool_calls
            if tool_calls:
                for call in tool_calls:
                    tool_name = call.function.name
                    tool_args = json.loads(call.function.arguments)
                    # 执行实际函数
                    func = plugin.tool_map[tool_name]
                    result = func(tool_args.get(plugin.param + "0"), self)
                    # assistant 调用工具记录
                    self.ctx.append({
                        "role": "assistant",
                        "tool_calls": [{
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }]
                    })
                    # 工具执行返回
                    self.ctx.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result
                    })
                prompt, _ = self.get_prompt()
        res = client.chat.completions.create(
            model=self.model_id,
            max_tokens=token_len if token_len is not None else self.max_resp_tokens,
            messages=prompt,
            stream=stream,
            n=1,  # 默认为1,对一个提问生成多少个回答
            temperature=1.2,  # 默认为1,0~2
        )
        if stream:
            return (x.choices[0].delta.content or '' for x in res)
        return res.choices[0].message.content

    def set_system(self, text):
        if len(self.ctx) and self.ctx[0].get('role') == 'system':
            self.ctx.pop(0)
        if text:
            self.ctx.insert(0, {"role": "system", "content": text})

    def instruction(self, query):
        if "#help" == query:
            return super().instruction(query) + \
                   "\n[#切换]切换模型" \
                   "\n[#system]设置助手角色&身份" \
                   "\n[#function]开关gpt外部函数" \
                   "\n[#addasst]向上下文中添加助手消息"
        elif "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            return self.set_model_attr(model_id)
        elif "#system" in query:
            system_text = query.replace("#system", "", 1).strip()
            self.set_system(system_text)
            return "セットアップ完了"
        elif "#function" in query:
            system_text = query.replace("#function", "", 1).strip()
            if system_text == "open" or system_text == "on":
                self.enable_function = True
            else:
                self.enable_function = False
            return "セットアップ完了"
        elif "#delfirst" in query:
            if self.ctx[0].get('role') == "system":
                self.ctx.pop(1)
            else:
                self.ctx.pop(0)
            return "[{}]已删除前项，会话信息如下：\n总轮数为{}\n总字符(or tokens)长度为{}" \
                .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
        elif "#addasst" in query:
            add_ctx = query.replace("#addasst", "", 1).strip()
            self.append_ctx(reply=add_ctx)
            return "[{}]已添加助手消息，会话信息如下：\n总轮数为{}\n总字符(or tokens)长度为{}" \
                .format(self.uid, len(self.ctx), self.get_prompt_len(self.join_ctx()))
        elif "#apikey" in query:
            apikey = query.replace("#apikey", "", 1).strip()
            self.getClient().api_key = apikey
            return "セットアップ完了"
        return super().instruction(query)

