from transformers import AutoTokenizer, AutoModel
from aichat import ChatAI


class ChatGLM(ChatAI):

    def __init__(self, **kw):
        super().__init__(**kw)

    def generate(self, prompt, stream=False):
        tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True)
        model = AutoModel.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True).half().cuda()
