import hashlib
import json
import httpx
from openai import OpenAI
from config import chat as chat_conf, display, match, cq_image_url_pattern, custom_token_len
from logger import logger
from plugin import GptFunction
from .chatai import ChatAI

_model_select = display(chat_conf['openai']['gpt']['model-select'])
_api_key = display(chat_conf['openai']['gpt']['api-key'])
_api_proxy = display(chat_conf['openai']['gpt']['proxy'])
client = OpenAI(api_key=_api_key, http_client=httpx.Client(proxy=_api_proxy)) \
    if _api_proxy else OpenAI(api_key=_api_key)


class ChatGPT(ChatAI):
    def __init__(self, model_id="gpt-4o-mini", default_system=None, model_select=None, **kw):
        super().__init__(model_id=model_id, **kw)
        self.model_id = None
        self.max_req_tokens = None
        self.max_resp_tokens = None
        self._cache_len = {}
        self.enable_function = False
        self._model_select = model_select or _model_select
        self.set_model_attr(model_id)
        self.set_system(default_system)

    def set_model_attr(self, model_id=None):
        model_attrs = self._model_select.get(model_id)
        if model_attrs is None:
            raise NotImplementedError(f"未找到{model_id}")
        max_tokens = model_attrs['max-tokens']
        max_resp_tokens = model_attrs['max-resp-tokens']
        self.model_id = model_id
        self.max_resp_tokens = max_resp_tokens
        self.max_req_tokens = max_tokens - max_resp_tokens

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
        images, query = match(cq_image_url_pattern, query)
        token_len, query = match(custom_token_len, query)
        if len(images):
            query = [{
                "type": "text",
                "text": query
            }, {
                "type": "image_url",
                "image_url": {
                    "url": images[0]
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

    def generate(self, query, jl, stream=False):
        prompt, token_len = self.get_prompt(query)
        if self.enable_function:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=prompt,
                functions=GptFunction.functions,
                function_call="auto",  # auto is default, but we'll be explicit
            )
            response_message = response["choices"][0]["message"]
            if response_message.get("function_call"):
                # Step 3: call the function
                # Note: the JSON response may not always be valid; be sure to handle errors
                function_name = response_message["function_call"]["name"]
                function_to_call = GptFunction.function_map[function_name]
                function_args = json.loads(response_message["function_call"]["arguments"])
                function_response = function_to_call(function_args.get(GptFunction.param_name), self)
                # Step 4: send the info on the function call and function response to GPT
                self.ctx.append(response_message)  # extend conversation with assistant's reply
                self.ctx.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
                prompt = self.get_prompt()
        jl.prompt_len = self.get_prompt_len(prompt)
        jl.before(query, prompt)
        res = client.chat.completions.create(
            model=self.model_id,
            max_tokens=token_len if token_len is not None else self.max_resp_tokens,
            messages=prompt,
            stream=stream,
            n=1,  # 默认为1,对一个提问生成多少个回答
            temperature=1.2,  # 默认为1,0~2
            # top_p = 1,                # 默认为1,0~1，效果类似temperature，不建议都用
            # stop = '',                # 遇到stop停止生成内容
            # presence_penalty = 2,     # 默认为0,-2~2，越大越允许跑题
            # frequency_penalty = 1.8,  # 默认为0,-2~2，越大越不允许复读机
            # logit_bias = None,        # 默认无,影响特定词汇的生成概率？
            # user = 'test',            # 默认无,用户名
        )
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
                   "\n[#切换]切换模型（例gpt-4/gpt-3.5-turbo）" \
                   "\n[#system]设置助手角色&身份" \
                   "\n[#function]开关gpt外部函数" \
                   "\n[#addasst]向上下文中添加助手消息"
        elif "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            try:
                if model_id == "preview":
                    model_id = "gpt-4-vision-preview"
                self.set_model_attr(model_id)
                return f"[{self.uid}]已切换模型{model_id}"
            except Exception as e:
                return str(e)
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
