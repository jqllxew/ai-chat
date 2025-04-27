import hashlib
import json
import time
from io import BytesIO

import plugin
from config import match, match_image, custom_token_len
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
        if self.max_req_tokens is None:
            self.set_model_attr(self.model_id)
            if self.max_req_tokens is None:
                raise RuntimeError(f"模型[{self.model_id}]不存在或未配置max_token")
        images, query = match_image(query)
        token_len, query = match(custom_token_len, query)
        if len(images):
            img = images[0]
            buffer = BytesIO()
            img.save(buffer, format="jpeg")
            url = tx_cos.upload(
                f"{self.model_id}/{self.uid}/{int(time.time() * 1000)}.jpg",
                buffer.getvalue()
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
        if self.enable_function:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=prompt,
                functions=plugin.functions,
                function_call="auto"
            )
            response_message = response.choices[0].message
            if response_message.function_call:
                function_name = response_message.function_call.name
                function_to_call = plugin.function_map[function_name]
                function_args = json.loads(response_message.function_call.arguments)
                function_response = function_to_call(function_args.get(plugin.param+"0"), self)
                self.ctx.append({
                    "role": "assistant",
                    "function_call": {
                        "name": function_name,
                        "arguments": json.dumps(function_args)
                    }
                })
                self.ctx.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(function_response)
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
        print(res)
        if stream:
            return (x.choices[0].delta.content or '' for x in res)
        return res.choices[0].message.content

    def set_system(self, text):
        if text:
            self.ctx.insert(0, {"role": "system", "content": text})
        else:
            if len(self.ctx) and self.ctx[0].get('role') == 'system':
                self.ctx.pop(0)

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
        return super().instruction(query)
