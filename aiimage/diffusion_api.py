import base64
import json
import random
from io import BytesIO

import requests
from PIL import Image

from config import image as image_conf, display
from abc import ABC

diffusion_conf = image_conf['diffusion']
prefix_prompt = display(diffusion_conf['prefix-prompt'])
default_neg_prompt = display(diffusion_conf['default-neg-prompt'])
api_conf = diffusion_conf['api']
url_txt2img = display(api_conf['url-txt2img'])
url_img2img = display(api_conf['url-img2img'])
image_max_width = display(api_conf['image-max-width'])
image_max_height = display(api_conf['image-max-height'])


class ApiImage(ABC):
    def __init__(self, width=680, height=680, prompt="", neg_prompt="", seed=0,
                 denoising_strength=.0, sampler_index="Euler a"):
        self.width = 680 if width == 0 else width  # 图片大小
        self.height = 680 if height == 0 else height
        self.denoising_strength = denoising_strength  # 降噪强度
        self.prompt = f"{prefix_prompt},{prompt}" if prefix_prompt else prompt  # 提示
        self.negative_prompt = default_neg_prompt if neg_prompt=="" else neg_prompt  # 负提示
        self.sampler_index = sampler_index  # 采样方法
        self.seed = seed if seed!= 0 else random.randint(0, 2147483647)  # 随机数
        self.styles = []  # 预先定义的样式列表
        self.subseed = -1  # 子随机数
        self.subseed_strength = 0  # 子随机种子的强度
        self.seed_resize_from_h = -1  # 从原始图像大小引入随机因素的大小
        self.seed_resize_from_w = -1
        self.batch_size = 1  # 批处理大小
        self.n_iter = 1  # 生成迭代次数
        self.steps = display(api_conf['steps'])  # 生成步数
        self.cfg_scale = display(api_conf['cfg-scale'])  # 引导规模
        self.restore_faces = display(api_conf['restore-faces'])  # 面部修复
        self.tiling = False  # 是否对图像进行平铺
        self.eta = 0  # 步长
        self.s_churn = 0  # 样式改变
        self.s_tmax = 0  # 样式温度范围
        self.s_tmin = 0
        self.s_noise = 1  # 样式噪声
        # extensions 扩展参数
        self.script_args = api_conf['script-args'] if display(api_conf['script-args']) is not None else []

    def send_api(self) -> (Image, str):
        """
        :return: image, str(err)
        """
        if isinstance(self, ApiTxt2Img):
            api_url = url_txt2img
        elif isinstance(self, ApiImg2Img):
            api_url = url_img2img
        else:
            return None, "diffusion_api unknown implement"
        print(f"prompt: {self.prompt}\nneg_prompt: {self.negative_prompt}\nscript_args: {self.script_args}")
        res = requests.post(api_url, json=self.__dict__)
        if res.status_code != 200:
            return None, str(res.content)
        ret = json.loads(res.content)
        if ret.get('nsfw_res') and ret['nsfw_res'][0]:
            return None, "抱歉~生成失败(nsfw尺度过大),绘制请适当描述衣着情况,参考dress或skirt或maid或添加sfw强调词"
        img_data = base64.b64decode(ret['images'][0])
        img = Image.open(BytesIO(img_data))
        return img, None


class ApiTxt2Img(ApiImage):
    def __init__(self, width: int, height: int, prompt: str,
                 neg_prompt: str, seed: int):
        super().__init__(width=width, height=height, prompt=prompt,
                         neg_prompt=neg_prompt, seed=seed)
        self.enable_hr = False  # 是否使用高分辨率
        # 首次生成图像的大小。
        self.firstphase_width = 0
        self.firstphase_height = 0


class ApiImg2Img(ApiImage):
    def __init__(self, width: int, height: int, prompt: str,
                 neg_prompt: str, img: Image, seed: int):
        super().__init__(width=width, height=height, denoising_strength=0.75,
                         prompt=prompt, neg_prompt=neg_prompt, seed=seed)
        # 初始化生成图像的输入图像
        self.init_images = [Image.fromarray(img).tobytes().decode('utf-8')]
        self.resize_mode = 0  # 图像大小是否在生成过程中改变
        self.mask = None  # 生成图像中应保留的区域
        self.mask_blur = 4
        self.inpainting_fill = 0
        self.inpaint_full_res = False
        self.inpaint_full_res_padding = 0
        self.inpainting_mask_invert = False
        self.override_settings = {}
        self.include_init_images = False


def inference(width, height, prompt, neg_prompt, seed, img=None) -> (Image, str):
    if width > image_max_width or height > image_max_height:
        return None, f"Error 抱歉,生成{width}x{height}图片已超过当前最大分辨率{image_max_width}x{image_max_height},请您调整参数"
    api: ApiImage
    if img is None:
        api = ApiTxt2Img(width, height, prompt, neg_prompt, seed)
    else:
        api = ApiImg2Img(width, height, prompt, neg_prompt, img, seed)
    return api.send_api()
