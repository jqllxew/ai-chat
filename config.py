import base64
import re
from io import BytesIO

import yaml
import os
import PIL
import requests
from PIL.Image import Image


class ConfDict(dict):
    def __init__(self, data: dict, miss=False):
        if data is None:
            data = {}
        super().__init__(data)
        self.data = data
        self.miss = miss

    def __getitem__(self, key):
        if key in self.data:
            val = self.data[key]
            if isinstance(val, dict) and not isinstance(val, ConfDict):
                self.data[key] = ConfDict(val)
            return self.data[key]
        return self.__class__.__missing__(self, key)

    def __missing__(self, key):
        val = ConfDict({}, True)
        self[key] = val
        return val


def display(_any):
    """
    :param _any: 任意参数
    :return:
    """
    if isinstance(_any, ConfDict) and _any.miss:
        return None
    else:
        return _any


config_path = "config.yaml"
if not os.path.exists(config_path):
    config_path = "config_example.yaml"
with open(config_path, "r", encoding="utf-8") as file:
    yaml_string = file.read()
_data = yaml.load(yaml_string, Loader=yaml.FullLoader)
server = ConfDict(_data.get('server'))
chat = ConfDict(_data.get('chat'))
qq = ConfDict(_data.get('qq'))
wx = ConfDict(_data.get('wx'))
image = ConfDict(_data.get('image'))
cos = ConfDict(_data.get('cos'))
fanyi = ConfDict(_data.get('fanyi'))
journal = ConfDict(_data.get('journal'))
plugin = ConfDict(_data.get('plugin'))


base64_image_pattern = "\\[base64=(.+?)]"  # base64图片
seed_pattern = "seed=(\\d+)"  # 随机数
width_height_pattern = "(\\d+)x(\\d+)"  # 宽高
ch_char_pattern = "[\u4e00-\u9fa5]+"  # 汉字
lora_pattern = "(&lt;|\\<)lora:(.+?)(&gt;|\\>)"  # lora
cq_speech_md5_pattern = "\\[CQ:.*file=([a-fA-F\\d]{32}).*voice_codec=1.*]"
cq_image_url_pattern = "\\[CQ:image.*url=(.+?)]"
custom_image_url_pattern = "img=(.*)"
custom_token_len = "token=(\\d+)"  # 自定义token数


def match(pattern, query):
    if query:
        _f = re.findall(pattern, query)
        query = re.sub(pattern, '', query)
        return _f, query
    return None, query


def match_image(query: str) -> (str, list[PIL.Image]):
    img_url, query = match(cq_image_url_pattern, query)
    img_base64, query = match(base64_image_pattern, query)
    img_custom, query = match(custom_image_url_pattern, query)
    images: list[PIL.Image] = []
    if img_url:
        response = requests.get(img_url[0])
        images.append(PIL.Image.open(BytesIO(response.content)))
    if img_base64:
        base64_data = base64.b64decode(img_base64[0])
        images.append(PIL.Image.open(BytesIO(base64_data)))
    if img_custom:
        print(img_custom[0])
        response2 = requests.get(img_custom[0])
        images.append(PIL.Image.open(BytesIO(response2.content)))
    return images, query
