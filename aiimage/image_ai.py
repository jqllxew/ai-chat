import random
import re
import time
from abc import ABC, abstractmethod
from io import BytesIO

import PIL
from PIL.Image import Image

import journal
from ai import ReplyAI
from config import match, match_image, seed_pattern, lora_pattern, ch_char_pattern, width_height_pattern
from cos import tx_cos
from journal import BaseDict
from plugin import youdao


class ImagePrompt(BaseDict):
    def __init__(self, query: str):
        super().__init__()
        self.img = None
        images, query = match_image(query)
        if len(images):
            self.img = images[0]
        seed, query = match(seed_pattern, query)
        width_height, query = match(width_height_pattern, query)
        lora, query = match(lora_pattern, query)
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
        lora = [x[1] for x in lora]
        self.prompt += f"<lora:{'>,<lora:'.join(lora)}>" if lora else ""

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

    @abstractmethod
    def generate(self, query: str, jl, ipt=None):
        raise NotImplementedError

    def upload(self, img: PIL.Image):
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
        ipt = ImagePrompt(query)
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
