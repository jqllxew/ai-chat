import base64
import random
import re
import time
from abc import ABC, abstractmethod
from io import BytesIO
import requests
from PIL.Image import Image

import journal
from config import image as image_conf
from ai import ReplyAI
from cos import tx_cos
from fanyi import youdao

diffusion_conf = image_conf['diffusion']
qq_image_pattern = "\\[CQ:image,.*url=(.+?)]"  # qq图片
wx_image_pattern = "\\[base64=(.+?)]"  # wx图片
seed_pattern = "seed=(\\d+)"  # 随机数
width_height_pattern = "(\\d+)x(\\d+)"  # 宽高
ch_char_pattern = "[\u4e00-\u9fa5]+"  # 汉字


class ImagePrompt:
    def __init__(self, query: str, from_type: str, model_id: str):
        self.model_id = model_id
        img_url = None
        img_base64 = None
        if from_type == 'qq':
            img_url = re.findall(qq_image_pattern, query)
            query = re.sub(qq_image_pattern, '', query)
        elif from_type == 'wx':
            img_base64 = re.findall(wx_image_pattern, query)
            query = re.sub(wx_image_pattern, '', query)
        seed = re.findall(seed_pattern, query)
        query = re.sub(seed_pattern, '', query)
        width_height = re.findall(width_height_pattern, query)
        query = re.sub(width_height_pattern, '', query)
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
        if img_url is not None and len(img_url) > 0:
            response = requests.get(img_url[0])
            self.img = Image.open(BytesIO(response.content))
        if img_base64 is not None and len(img_base64) > 0:
            base64_data = base64.b64decode(img_base64[0])
            self.img = Image.open(BytesIO(base64_data))


class ImageAI(ReplyAI, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def generate(self, prompt: ImagePrompt):
        raise NotImplementedError

    def upload(self, img: Image):
        try:
            buffer = BytesIO()
            img.save(buffer, format="png")
            return tx_cos.upload(
                f"{self.model_id}/{self.uid}/{img.width}x{img.height}/{int(time.time()*1000)}.png",
                buffer.getvalue()
            ), None
        except Exception as e:
            return None, str(e)

    def reply(self, query: str, before=..., after=..., error=...):
        """
        :param before:
        :param after:
        :param error:
        :param query: 绘画要求
        :return: reply image_path
        """
        jl = journal.lifecycle(**self.__dict__,
                               _before=before, _after=after, _error=error)
        ipt = ImagePrompt(query, self.from_type, self.model_id)
        jl.before(query, f"{ipt.prompt}|neg={ipt.neg_prompt}|{ipt.width}x{ipt.height}")
        now = time.time()
        url, err = self.generate(ipt)
        generate_seconds = time.time() - now
        reply_format = "提示词：{}\n负提示：{}\n随机数：{}\n耗时秒：{:.3f}\n宽高：{}\n".format(
            ipt.prompt if ipt.img is None else (ipt.prompt + '+[图片参数]'),
            "默认" if ipt.neg_prompt == "" else ipt.neg_prompt,
            ipt.seed, generate_seconds, f"{ipt.width}x{ipt.height}")
        if err is None:
            if self.from_type == 'qq':
                reply_format += f"[CQ:image,file={url}]"
            elif self.from_type == 'wx':
                reply_format += f"[image={url}]"
            else:
                reply_format += url
            jl.after(reply_format)
        else:
            reply_format += f"generate error because {err}"
            jl.error(err)
        return reply_format
