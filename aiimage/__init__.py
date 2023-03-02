from aiimage.diffusion import Diffusion
from aiimage.image_ai import ImageAI
from config import image as image_conf, display

user_models: dict[str, ImageAI] = {}


def u_model(uid, from_type=None) -> ImageAI:
    m = user_models.get(uid)
    if m is None:
        if display(image_conf['diffusion']):
            m = Diffusion(
                uid=uid,
                from_type=from_type,
                model_id=image_conf['diffusion']['uri'])
        elif display(image_conf['diffusers']):
            from aiimage.diffusers import Diffusers
            m = Diffusers(
                uid=uid,
                from_type=from_type,
                model_id=image_conf['diffusers']['model-id'])
        user_models[uid] = m
    return m


def draw(uid: str, query: str, from_type: str):
    return u_model(uid, from_type).reply(query)


__all__ = [
    "draw",
    "u_model",
    "ImageAI",
    "Diffusion"
]
