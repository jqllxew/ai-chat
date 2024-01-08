import hashlib
import json
import openai
import tiktoken

from aiimage.image_ai import replace_image
from config import chat as chat_conf, display
from logger import logger
from plugin import GptFunction
from .chatai import ChatAI

_model_select = display(chat_conf['openai']['gpt']['model-select'])


def _num_tokens_from_messages(messages, model="gpt-3.5-turbo") -> int:
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            if not isinstance(value, str):
                value = str(value)
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    if num_tokens > 0:
        num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


class OpenAI(ChatAI):
    def __init__(self, api_key=None, proxy=None, model_id=None, **kw):
        super().__init__(**kw)
        if api_key:
            openai.api_key = api_key
        openai.proxy = {
            'http': proxy,
            'https': proxy
        } if proxy else None
        self.model_id = model_id or "text-davinci-003"
        self.max_req_tokens = None
        self.max_resp_tokens = None
        self.set_model_attr()

    def set_model_attr(self):
        model_attrs = _model_select.get(self.model_id)
        if model_attrs is None:
            raise NotImplementedError(f"未找到{self.model_id}")
        max_tokens = model_attrs['max-tokens']
        max_resp_tokens = model_attrs['max-resp-tokens']
        self.max_resp_tokens = max_resp_tokens
        self.max_req_tokens = max_tokens - max_resp_tokens

    def set_system(self, system_text):
        self.ctx.insert(0, system_text)

    def join_ctx(self, sep="\n\n"):
        return sep.join(self.ctx)

    def get_prompt(self, query=""):
        prompt = super().get_prompt(query)
        while self.get_prompt_len(prompt) > self.max_req_tokens:
            logger.warn(f"[{self.model_id}]{self.uid}:prompt_len "
                        f"{self.get_prompt_len(prompt)} > {self.max_req_tokens}")
            if len(self.ctx) > 1:
                self.ctx.pop(0)
            else:
                raise RuntimeError("prompt text too long")
            prompt = super().get_prompt()
        return prompt

    def generate(self, query, jl, stream=False):
        prompt = self.get_prompt(query)
        jl.prompt_len = self.get_prompt_len(prompt)
        jl.before(query, prompt)
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

    def instruction(self, query, chat_type='gpt'):
        if "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            try:
                self.model_id = model_id
                self.set_model_attr()
                return f"[{self.uid}]已切换模型{model_id}"
            except Exception as e:
                return str(e)
        return super().instruction(query)


class ChatGPT(OpenAI):
    def __init__(self, api_key=None, model_id=None, default_system=None, **kw):
        super().__init__(api_key=api_key, model_id=model_id or "gpt-3.5-turbo", **kw)
        if default_system:
            self.set_system(default_system)
        self._cache_len = {}
        self.enable_function = False

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        reply and self.ctx.append({"role": "assistant", "content": reply})

    def join_ctx(self, sep=...):
        return self.ctx

    def get_prompt_len(self, prompt):
        _hash = hashlib.md5(str(prompt).encode()).hexdigest()
        if self._cache_len.get('_hash') != _hash:
            self._cache_len['_hash'] = _hash
            self._cache_len['_len'] = _num_tokens_from_messages(prompt, self.model_id)
        return self._cache_len['_len']

    def get_prompt(self, query=""):
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
        return self.ctx

    def generate(self, query, jl, stream=False):
        prompt = self.get_prompt(query)
        if replace_image(query) == "":  # 只有图片
            print("only image")
            return ""
        if self.enable_function:
            response = openai.ChatCompletion.create(
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
        res = openai.ChatCompletion.create(
            model=self.model_id,
            max_tokens=self.max_resp_tokens,
            messages=prompt,
            stream=stream,
            n=1,  # 默认为1,对一个提问生成多少个回答
            temperature=1,  # 默认为1,0~2，数值越高创造性越强
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
        elif "#function" in query:
            system_text = query.replace("#function", "", 1).strip()
            if system_text == "open" or system_text == "on":
                self.enable_function = True
            else:
                self.enable_function = False
            return "设置成功"
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
        return super().instruction(query, chat_type)
