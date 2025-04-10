from abc import ABC, abstractmethod

import anthropic
import httpx
from openai import OpenAI

from config import chat as chat_conf, display


class ReplyAI(ABC):
    def __init__(self, uid, from_type, model_id=None):
        self.uid = uid
        self.from_type = from_type
        self.model_id = model_id

    @abstractmethod
    def generate(self, query: str):
        """
        :return: text or Iterator
        """
        raise NotImplementedError

    @abstractmethod
    def reply(self, query: str):
        """
        :param query: 文本消息
        :return: reply generate()
        """
        raise NotImplementedError


class OpenAIClient:
    def __init__(self):
        self.model_select = display(chat_conf['openai']['gpt']['model-select'])
        _api_key = display(chat_conf['openai']['gpt']['api-key'])
        if _api_key:
            _api_proxy = display(chat_conf['openai']['gpt']['proxy'])
            _base_url = display(chat_conf['openai']['gpt']['base-url'])
            self.client = OpenAI(api_key=_api_key, base_url=_base_url, http_client=httpx.Client(proxy=_api_proxy)) \
                if _api_proxy else OpenAI(api_key=_api_key)
        else:
            raise RuntimeError("未找到apiKey")


class ClaudeClient:
    def __init__(self):
        self.model_select = display(chat_conf['anthropic']['claude']['model-select'])
        _api_key = display(chat_conf['anthropic']['claude']['api-key'])
        if _api_key:
            _api_proxy = display(chat_conf['anthropic']['claude']['proxy'])
            _base_url = display(chat_conf['anthropic']['claude']['base-url'])
            self.client = anthropic.Anthropic(api_key=_api_key, base_url=_base_url, proxies=_api_proxy)
        else:
            raise RuntimeError("未找到apiKey")
