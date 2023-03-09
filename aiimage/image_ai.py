import base64
import random
import re
import time
from abc import ABC, abstractmethod
from io import BytesIO

import PIL
import requests
from PIL.Image import Image

import journal
from config import image as image_conf
from ai import ReplyAI
from cos import tx_cos
from fanyi import youdao
from journal import BaseDict

diffusion_conf = image_conf['diffusion']
qq_image_pattern = "\\[CQ:image,.*url=(.+?)]"  # qq图片
wx_image_pattern = "\\[base64=(.+?)]"  # wx图片
general_image_pattern = "\\[image=(.+?)]"
seed_pattern = "seed=(\\d+)"  # 随机数
width_height_pattern = "(\\d+)x(\\d+)"  # 宽高
ch_char_pattern = "[\u4e00-\u9fa5]+"  # 汉字


class ImagePrompt(BaseDict):
    def __init__(self, query: str, from_type: str):
        super().__init__()
        img_url = None
        img_base64 = None
        if from_type == 'qq':
            img_url = re.findall(qq_image_pattern, query)
            query = re.sub(qq_image_pattern, '', query)
        elif from_type == 'wx':
            img_base64 = re.findall(wx_image_pattern, query)
            query = re.sub(wx_image_pattern, '', query)
        else:
            img_url = re.findall(general_image_pattern, query)
            query = re.sub(general_image_pattern, '', query)
        seed = re.findall(seed_pattern, query)
        query = re.sub(seed_pattern, '', query)
        width_height = re.findall(width_height_pattern, query)
        query = re.sub(width_height_pattern, '', query)
        prompts = query.split('neg_prompt=')
        self.origin_prompt = prompts[0]
        self.origin_neg_prompt = prompts[1]
        if re.search(ch_char_pattern, query):  # 翻译汉字
            query = youdao.chs2en(query)
        prompts = query.split('neg_prompt=')
        self.prompt = prompts[0]
        self.neg_prompt = ""
        if len(prompts) == 2:
            self.neg_prompt = prompts[1]
        self.width = 576
        self.height = 576
        if len(width_height) > 0:
            self.width = int(width_height[0][0])
            self.height = int(width_height[0][1])
        self.seed = random.randint(0, 2147483647) if len(seed) == 0 else int(seed[0])
        self.img = None
        self.img_url = None
        if img_url and len(img_url) > 0:
            self.img_url = img_url[0]
            response = requests.get(self.img_url)
            self.img = PIL.Image.open(BytesIO(response.content))
        if img_base64 and len(img_base64) > 0:
            base64_data = base64.b64decode(img_base64[0])
            self.img = PIL.Image.open(BytesIO(base64_data))

    def prompt_len(self):
        return len(self.prompt) + len(self.neg_prompt)


class ImageReply(BaseDict):
    def __init__(self, prompt, neg_prompt, size, seed, elapsed_sec, style):
        super().__init__()
        self.prompt=prompt
        self.neg_prompt=neg_prompt
        self.size=size
        self.seed=seed
        self.elapsed_sec=elapsed_sec
        self.style=style
        self.image=None
        self.err = None


class ImageAI(ReplyAI, ABC):
    def __init__(self, style=None, **kwargs):
        super().__init__(**kwargs)
        self.style = style

    @abstractmethod
    def generate(self, prompt: ImagePrompt):
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
        if not jl:
            jl = journal.default_journal(**self.__dict__)
        ipt = ImagePrompt(query, self.from_type)
        jl.before(query, ipt)
        now = time.time()
        url, err = self.generate(ipt)
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
