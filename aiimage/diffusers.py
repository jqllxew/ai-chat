from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler
import torch
from PIL import Image
from threading import Lock

from aiimage.image_ai import ImageAI, ImagePrompt
from config import image as image_conf, display
from logger import logger

prefix_prompt = display(image_conf['prefix-prompt'])
default_neg_prompt = display(image_conf['default-neg-prompt'])
_conf = image_conf['diffusers']

i2i_support = display(_conf['i2i-support'])
image_max_width = display(_conf['image-max-width'])
image_max_height = display(_conf['image-max-height'])
device = "cuda" if torch.cuda.is_available() else "cpu"  # 判断设备
lock = Lock()


def _txt2img(prompt, neg_prompt, guidance, steps, width, height, generator, model_id, scheduler) -> Image:
    with lock:
        # 构建通道对象函数
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            scheduler=scheduler)
        pipe = pipe.to(device)
        try:
            result = pipe(
                prompt,
                negative_prompt=neg_prompt,
                num_inference_steps=int(steps),
                guidance_scale=guidance,
                width=width,
                height=height,
                generator=generator)
        finally:
            torch.cuda.empty_cache()
    return result.images[0]


def _img2img(prompt, neg_prompt, img, strength, guidance, steps, generator, model_id, scheduler) -> Image:
    ratio = 1
    if img.width > image_max_width or img.height > image_max_height:
        ratio = min(image_max_height / img.height, image_max_width / img.width)
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    with lock:
        pipe_i2i = StableDiffusionImg2ImgPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            scheduler=scheduler)
        pipe_i2i = pipe_i2i.to(device)
        try:
            result = pipe_i2i(
                prompt,
                negative_prompt=neg_prompt,
                image=img,
                num_inference_steps=int(steps),
                strength=strength,
                guidance_scale=guidance,
                generator=generator)
        finally:
            torch.cuda.empty_cache()
    return result.images[0]


def inference(prompt, guidance=None, steps=None, width=512, height=512, seed=0, img=None,
              strength=0.5, neg_prompt="", auto_prefix=False, model_id=None) -> (Image, str):
    model_id = model_id or display(_conf['model-id'])
    if model_id is None:
        return None, "model_id is None"
    if width > image_max_width or height > image_max_height:
        return None, f"Error 抱歉,生成{width}x{height}图片已超过当前最大分辨率{image_max_width}x{image_max_height},请您调整参数"
    if guidance is None:
        guidance = display(_conf['guidance']) or 7
    if steps is None:
        steps = display(_conf['steps']) or 20
    generator = torch.Generator('cuda').manual_seed(seed) if seed != 0 else None
    prompt = f"{prefix_prompt},{prompt}" if auto_prefix and prefix_prompt else prompt
    if neg_prompt == "":
        neg_prompt = default_neg_prompt
    logger.debug(f"[diffusers] prompt: {prompt}\nneg_prompt: {neg_prompt}")
    try:
        scheduler = DPMSolverMultistepScheduler.from_pretrained(model_id, subfolder="scheduler")  # 创建调度器
        if i2i_support and img is not None:
            return _img2img(prompt, neg_prompt, img, strength, guidance, steps, generator, model_id, scheduler), None
        else:
            return _txt2img(prompt, neg_prompt, guidance, steps, width, height, generator, model_id, scheduler), None
    except Exception as e:
        print(e)
        return None, str(e)


class Diffusers(ImageAI):
    def generate(self, ipt: ImagePrompt):
        img, err = inference(auto_prefix=True, **ipt.__dict__)
        if err:
            return None, err
        return self.upload(img)

    def reply(self, query: str, _before=None, _after=None, _error=None):
        return super().reply(
            query=query,
            _before=lambda q, p: f"[diffusers]{self.uid}-query:{q}\nprompt:{p}",
            _after=lambda x: f"[diffusers]{self.uid}-reply:{x}",
            _error=lambda x: f"[diffusers]{self.uid}-error:{x}"
        )
