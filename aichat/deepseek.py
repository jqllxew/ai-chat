
from openai import OpenAI

from aichat.gpt import ChatGPT
from config import chat as chat_conf, display

_model_select = display(chat_conf['deepseek']['model-select'])
_api_key = display(chat_conf['deepseek']['api-key'])
client = OpenAI(api_key=_api_key, base_url="https://api.deepseek.com")


class DeepSeek(ChatGPT):

    def __init__(self, model_id="deepseek-reasoner", default_system=None, **kw):
        super().__init__(model_id=model_id, default_system=default_system, model_select=_model_select, **kw)

    def getClient(self):
        return client
