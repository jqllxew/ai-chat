from aiimage.dallE import DallE
from aiimage.diffusion import Diffusion
from aiimage.image_ai import ImageAI
from config import image as image_conf, display
from logger import logger

user_models: dict[str, ImageAI] = {}


def u_change_model(uid, image_type='', from_type=None, model_id=None):
    if 'diffusion' == image_type or 'sd' == image_type:
        user_models[uid] = Diffusion(
            uid=uid, from_type=from_type,
            uri=display(image_conf['diffusion']['uri']),
            model_id=model_id or display(image_conf['diffusion']['model-id']))
    elif 'diffusers' == image_type:
        from aiimage.diffusers import Diffusers
        user_models[uid] = Diffusers(
            uid=uid, from_type=from_type,
            model_id=model_id or display(image_conf['diffusers']['model-id']))
    elif 'dalle' == image_type:
        user_models[uid] = DallE(uid=uid, from_type=from_type, model_id=model_id or "dall-e-3")
    else:
        return f"未找到 {image_type}"


def u_model(uid, from_type=None) -> ImageAI:
    if not user_models.get(uid):
        u_change_model(uid, 'diffusion', from_type)
    return user_models.get(uid)


def draw(uid: str, query: str, from_type: str, use_template=True) -> str:
    reply = u_model(uid, from_type).reply(query)
    if reply.err:
        image = reply.err
    elif from_type == 'qq':
        image = f"[CQ:image,file={reply.image}]"
    elif from_type == 'wx':
        image = f"[image={reply.image}]"
    else:
        image = reply.image
    if use_template:
        template = display(image_conf['reply-template'])
        try:
            return template.format(
                prompt=reply.prompt, neg_prompt=reply.neg_prompt or "默认",
                seed=reply.seed, elapsed_sec=reply.elapsed_sec,
                size=reply.size, image=image)
        except Exception as e:
            logger.error(f"[aiimage]reply-template模板错误\nerr:{e}")
    return image


__all__ = [
    "draw",
    "u_model",
    "ImageAI",
    "Diffusion"
]
