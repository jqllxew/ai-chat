import random
import re
import time
from io import BytesIO
import requests
from PIL import Image
from aiimage import diffusion_local
from aiimage import diffusion_api
from cos import tx_cos
from fanyi import youdao
from config import image as image_conf, display

diffusion_conf = image_conf['diffusion']
qq_image_pattern = "\\[CQ:image,.*url=(.+?)]"  # qq图片
seed_pattern = "seed=(\\d+)"  # 随机数
width_height_pattern = "(\\d+)x(\\d+)"  # 宽高
ch_char_pattern = "[\u4e00-\u9fa5]+"  # 汉字


class ImageQuery(object):
    def __init__(self, query: str, from_type: str):
        img_url = None
        if from_type == 'qq':
            img_url = re.findall(qq_image_pattern, query)
            query = re.sub(qq_image_pattern, '', query)
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
        self.image = None
        if img_url is not None and len(img_url) > 0:
            response = requests.get(img_url[0])
            self.image = Image.open(BytesIO(response.content))
        self.generate_image = None
        self.generate_err = None
        self.generate_image_path = None
        self.generate_seconds = .0


def _generate_by_image_query(image_query: ImageQuery):
    now = time.time()
    if display(diffusion_conf['local']) is not None:
        image, err = diffusion_local.inference(
            prompt=image_query.prompt,
            guidance=diffusion_conf['local']['guidance'],
            steps=diffusion_conf['local']['steps'],
            width=image_query.width,
            height=image_query.height,
            seed=image_query.seed,
            img=image_query.image,
            neg_prompt=image_query.neg_prompt,
            auto_prefix=True
        )
    elif display(diffusion_conf['api']) is not None:
        image, err = diffusion_api.inference(
            prompt=image_query.prompt,
            neg_prompt=image_query.neg_prompt,
            width=image_query.width,
            height=image_query.height,
            seed=image_query.seed,
            img=image_query.image
        )
    else:
        image = None
        err = "_generate_by_image_query unknown implement"
    image_query.generate_seconds = time.time() - now
    image_query.generate_image = image
    image_query.generate_err = err


separator_pattern = "\\s*([,，\\?\\/!:;-])\\s*"


def generate_by_query(uid, query, from_type) -> ImageQuery:
    image_query = ImageQuery(query, from_type)  # 提取参数
    try:
        _generate_by_image_query(image_query)
        if image_query.generate_err is None:
            buffer = BytesIO()
            image_query.generate_image.save(buffer, format="png")
            binary_data = buffer.getvalue()
            prompt = re.sub(separator_pattern, '_', image_query.prompt)
            image_query.generate_image_path = tx_cos.upload(
                f"{uid}/{image_query.width}x{image_query.height}/{prompt.replace(' ','-')}_{image_query.seed}.png",
                binary_data)
            print(f"[image]generate path {image_query.generate_image_path}")
    except Exception as e:
        print(e)
        image_query.generate_err = e
    return image_query
