from ai.base import OpenAIClient
from ai.image.imageai import ImageAI


class DallE(ImageAI):

    def __init__(self, model_id, **keyword):
        super().__init__(model_id=model_id or "dall-e-3", **keyword)
        self.client = OpenAIClient().client

    # Must be one of 1024x1024, 1792x1024, or 1024x1792 for dall-e-3 models.
    def generate(self, ipt):
        ipt.width = 1792 if ipt.width >= 1792 else 1024
        ipt.height = 1792 if ipt.height >= 1792 else 1024
        res = self.client.images.generate(
            model=self.model_id,
            prompt=ipt.prompt,
            quality="standard",
            n=1,
            size=f"{ipt.width}x{ipt.height}"
        )
        return res.data[0].url
