import base64
import io
import json
import random
from io import BytesIO
import requests
from PIL import Image
from aiimage.image_ai import ImageAI, ImagePrompt
from config import image as image_conf, display
from abc import ABC

from journal import BaseDict
from logger import logger

prefix_prompt = display(image_conf['prefix-prompt'])
default_neg_prompt = display(image_conf['default-neg-prompt'])
_conf = image_conf['diffusion']
image_max_width = display(_conf['image-max-width'])
image_max_height = display(_conf['image-max-height'])


class ApiImage(BaseDict):
    def __init__(self, width=0, height=0, prompt="", neg_prompt="", seed=0, denoising_strength=.0,
                 sampler_index="Euler a", uri=None, **kwargs):
        super().__init__()
        self.width = width or 576  # 图片大小
        self.height = height or 576
        self.denoising_strength = denoising_strength  # 降噪强度
        self.prompt = f"{prefix_prompt},{prompt}" if prefix_prompt else prompt  # 提示
        self.negative_prompt = f"{default_neg_prompt},{neg_prompt}" if neg_prompt else default_neg_prompt  # 负提示
        self.sampler_index = sampler_index  # 采样方法
        self.seed = seed if seed!= 0 else random.randint(0, 2147483647)  # 随机数
        self.styles = []  # 预先定义的样式列表
        self.subseed = -1  # 子随机数
        self.subseed_strength = 0  # 子随机种子的强度
        self.seed_resize_from_h = -1  # 从原始图像大小引入随机因素的大小
        self.seed_resize_from_w = -1
        self.batch_size = 1  # 批处理大小
        self.n_iter = 1  # 生成迭代次数
        self.steps = display(_conf['steps'])  # 生成步数
        self.cfg_scale = display(_conf['cfg-scale'])  # 引导规模
        self.restore_faces = display(_conf['restore-faces'])  # 面部修复
        self.tiling = False  # 是否对图像进行平铺
        self.eta = 0  # 步长
        self.s_churn = 0  # 样式改变
        self.s_tmax = 0  # 样式温度范围
        self.s_tmin = 0
        self.s_noise = 1  # 样式噪声
        # extensions 扩展参数
        self.script_args = display(_conf['script-args']) or []
        self.uri = uri or display(_conf['uri'])

    def send_api(self) -> (Image, str):
        """
        :return: image, str(err)
        """
        if self.width > image_max_width or self.height > image_max_height:
            return None, f"Error 抱歉,生成{self.width}x{self.height}图片" \
                         f"已超过当前最大分辨率{image_max_width}x{image_max_height},请您调整参数"
        if isinstance(self, ApiTxt2Img):
            api_url = self.uri + '/sdapi/v1/txt2img'
        elif isinstance(self, ApiImg2Img):
            api_url = self.uri + '/sdapi/v1/img2img'
        else:
            return None, "diffusion_api unknown implement"
        logger.debug(f"[{self.uri}]prompt: {self.prompt}\n"
                     f"neg_prompt: {self.negative_prompt}\n"
                     f"script_args: {self.script_args}")
        sess = requests.Session()
        proxy = display(_conf['proxy'])
        if proxy:
            sess.proxies = {'http': proxy, 'https': proxy}
        res = sess.post(api_url, json=self.to_dict('uri'), timeout=120)
        if res.status_code != 200:
            return None, str(res.content)
        ret = json.loads(res.content)
        if ret.get('nsfw_res') and ret['nsfw_res'][0]:
            return None, "抱歉~生成失败(nsfw尺度过大),绘制请适当描述衣着情况,参考dress或skirt或maid或添加sfw强调词"
        img_data = base64.b64decode(ret['images'][0])
        img = Image.open(BytesIO(img_data))
        return img, None


class ApiTxt2Img(ApiImage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enable_hr = False  # 是否使用高分辨率
        # 首次生成图像的大小。
        self.firstphase_width = 0
        self.firstphase_height = 0


class ApiImg2Img(ApiImage):
    def __init__(self, img: Image, **kwargs):
        super().__init__(denoising_strength=0.75, **kwargs)
        # 初始化生成图像的输入图像
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        self.init_images = [base64.b64encode(buffered.getvalue()).decode()]
        self.resize_mode = 0  # 图像大小是否在生成过程中改变
        self.mask = None  # 生成图像中应保留的区域
        self.mask_blur = 4
        self.inpainting_fill = 0
        self.inpaint_full_res = False
        self.inpaint_full_res_padding = 0
        self.inpainting_mask_invert = False
        self.override_settings = {}
        self.include_init_images = False


def inference(img=None, **kwargs) -> (Image, str):
    try:
        api: ApiImage
        if img is None:
            api = ApiTxt2Img(**kwargs)
        else:
            api = ApiImg2Img(img=img, **kwargs)
        return api.send_api()
    except Exception as e:
        return None, str(e)


class Diffusion(ImageAI):
    def __init__(self, uri=None, **kwargs):
        super().__init__(**kwargs)
        self.uri = uri or self.model_id
        self.model_id = self.model_id or self.uri

    def generate(self, ipt: ImagePrompt):
        img, err = inference(uri=self.uri, **ipt.to_dict())
        if err:
            return None, err
        return self.upload(img)
