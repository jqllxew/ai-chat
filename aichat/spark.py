import base64
import hashlib
import hmac
import _thread as thread
import json
import ssl
import threading
import time
from datetime import datetime
from queue import Queue
from time import mktime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
import journal
from aichat import ChatAI
import websocket
from config import chat as chat_conf, display, match, custom_token_len


_model_select = display(chat_conf['iflytek']['spark']['model-select'])

def on_error(ws, error):
    print("### error:", error)

# 收到websocket关闭的处理
def on_close(ws, one, two):
    print(" ")

# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question, token_len=ws.token_len))
    ws.send(data)

def gen_params(appid, domain, question, token_len):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "random_threshold": 0.5,
                "max_tokens": token_len if token_len is not None else 2048,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


def queue_generator(ws, queue, timeout=10):
    then = time.time()
    while True:
        if queue.empty():
            time.sleep(0.5)
            now = time.time()
            if now - then > timeout:
                print("spark queue timeout")
                break
        else:
            message = queue.get()
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                print(f'请求错误: {code}, {data}')
                if data:
                    yield data.get('header', {}).get('message')
                ws.close()
                break
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                yield content
                if status == 2:
                    ws.close()
                    break


class ChatSpark(ChatAI):

    def __init__(self, app_id, api_key, api_secret, model_id=None, **kw):
        super().__init__(**kw)
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.model_id = None
        self.max_length = None
        self.host = None
        self.path = None
        self.spark_url = None
        self.domain = None
        self.set_model_attr(model_id or "sparkv3.5")

    def set_model_attr(self, model_id):
        model_attrs = _model_select.get(model_id)
        if model_attrs is None:
            raise NotImplementedError(f"未找到{self.model_id}")
        spark_url = model_attrs['spark-url']
        self.spark_url = spark_url
        parser = urlparse(spark_url)
        self.host = parser.netloc
        self.path = parser.path
        self.domain = model_attrs['domain']
        self.max_length = model_attrs['max-length'] or 2048
        self.model_id = model_id

    def _create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.spark_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url

    def generate(self, query: str, stream=False):
        websocket.enableTrace(False)
        ws_url = self._create_url()
        ws = websocket.WebSocketApp(url=ws_url,
                                    on_error=on_error,
                                    on_close=on_close,
                                    on_open=on_open)
        prompt, token_len = self.get_prompt(query)
        message_queue = Queue()
        # message_gen = message_generator(message_queue)
        # next(message_gen)  # Start the generator
        ws.on_message = lambda _ws, message: message_queue.put(message)
        ws.appid = self.app_id
        ws.question = prompt
        ws.domain = self.domain
        ws.token_len = token_len
        _thread = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
        _thread.start()
        if stream:
            return queue_generator(ws, message_queue)
        else:
            _thread.join()
            result = ''.join(queue_generator(ws, message_queue))
            return result

    def set_system(self, system_text):
        self.append_ctx(query=system_text)

    def append_ctx(self, query=None, reply=None):
        query and self.ctx.append({"role": "user", "content": query})
        reply and self.ctx.append({"role": "assistant", "content": reply})

    def get_prompt(self, query=""):
        token_len, query = match(custom_token_len, query)
        self.append_ctx(query)
        while self.get_prompt_len(self.ctx) > self.max_length:
            self.ctx.pop(0)
        return self.ctx, int(token_len[0]) if token_len else None

    def instruction(self, query):
        if "#切换" in query:
            model_id = query.replace("#切换", "", 1).strip()
            try:
                self.set_model_attr(model_id)
                return f"[{self.uid}]已切换模型{model_id}"
            except Exception as e:
                return str(e)
        return super().instruction(query)