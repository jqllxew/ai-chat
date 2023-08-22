import base64
import random
import re
import time
from abc import ABC
from io import BytesIO

import PIL
import requests
from PIL.Image import Image

import journal
from config import image as image_conf
from ai import ReplyAI
from cos import tx_cos
from plugin import youdao
from journal import BaseDict

diffusion_conf = image_conf['diffusion']
qq_image_pattern = "\\[CQ:image,.*url=(.+?)]"  # qq图片
wx_image_pattern = "\\[base64=(.+?)]"  # wx图片
general_image_pattern = "\\[image=(.+?)]"
seed_pattern = "seed=(\\d+)"  # 随机数
width_height_pattern = "(\\d+)x(\\d+)"  # 宽高
ch_char_pattern = "[\u4e00-\u9fa5]+"  # 汉字
lora_pattern = "(&lt;|\\<)lora:(.+?)(&gt;|\\>)"  # lora


def _match(pattern, query):
    match = re.findall(pattern, query)
    query = re.sub(pattern, '', query)
    return match, query


def replace_image(query):
    query = re.sub(qq_image_pattern, '', query)
    query = re.sub(wx_image_pattern, '', query)
    return query.strip()


class ImagePrompt(BaseDict):
    def __init__(self, query: str, from_type: str):
        super().__init__()
        img_url = None
        img_base64 = None
        if from_type == 'qq':
            img_url, query = _match(qq_image_pattern, query)
        elif from_type == 'wx':
            img_base64, query = _match(wx_image_pattern, query)
        else:
            img_url, query = _match(general_image_pattern, query)
        seed, query = _match(seed_pattern, query)
        width_height, query = _match(width_height_pattern, query)
        lora, query = _match(lora_pattern, query)
        prompts = query.split('neg_prompt=')
        self.origin_prompt = prompts[0]
        self.origin_neg_prompt = prompts[1] if len(prompts) > 1 else ""
        if re.search(ch_char_pattern, query):  # 翻译汉字
            query = youdao.chs2en(query)
        prompts = query.split('neg_prompt=')
        self.prompt = prompts[0]
        self.neg_prompt = prompts[1] if len(prompts) > 1 else ""
        self.width = 576
        self.height = 576
        if len(width_height) > 0:
            self.width = int(width_height[0][0])
            self.height = int(width_height[0][1])
        self.seed = random.randint(0, 2147483647) if len(seed) == 0 else int(seed[0])
        self.img = None
        self.img_url = None
        lora = [x[1] for x in lora]
        self.prompt += f"<lora:{'>,<lora:'.join(lora)}>" if lora else ""
        if img_url:
            self.img_url = img_url[0]
            response = requests.get(self.img_url)
            self.img = PIL.Image.open(BytesIO(response.content))
        if img_base64:
            base64_data = base64.b64decode(img_base64[0])
            self.img = PIL.Image.open(BytesIO(base64_data))

    def prompt_len(self):
        return len(self.prompt) + len(self.neg_prompt)


class ImageReply(BaseDict):
    def __init__(self, prompt, neg_prompt, size, seed, elapsed_sec, style):
        super().__init__()
        self.prompt = prompt
        self.neg_prompt = neg_prompt
        self.size = size
        self.seed = seed
        self.elapsed_sec = elapsed_sec
        self.style = style
        self.image = None
        self.err = None


class ImageAI(ReplyAI, ABC):
    def __init__(self, style=None, **kwargs):
        super().__init__(**kwargs)
        self.style = style

    # @abstractmethod
    def generate(self, query: str, jl, ipt=None):
        raise NotImplementedError

    def upload(self, img: Image):
        try:
            store_dir = tx_cos.store_dir("img")
            buffer = BytesIO()
            img.save(buffer, format="png")
            return tx_cos.upload(
                f"{store_dir}/{self.model_id}/{self.uid}/"
                f"{img.width}x{img.height}/{int(time.time() * 1000)}.png",
                buffer.getvalue()
            ), None
        except Exception as e:
            return None, str(e)

    def reply(self, query: str, jl: journal.Journal = None):
        """
        :param jl: journal环绕调用
        :param query: 绘画要求
        :return: reply image_path
        """
        jl = journal.default_journal(**self.__dict__)
        now = time.time()
        ipt = ImagePrompt(query, self.from_type)
        url, err = self.generate(query, jl, ipt)
        elapsed_sec = time.time() - now
        reply = ImageReply(ipt.prompt, ipt.neg_prompt, f"{ipt.width}x{ipt.height}",
                           ipt.seed, elapsed_sec, self.style)
        if err:
            reply.err = err
            jl.error(err)
        else:
            reply.image = url
            jl.after(reply)
        return reply
