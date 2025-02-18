from aiimage.image_ai import ImageAI
import openai


class DallE(ImageAI):

    def generate(self, query: str, jl, ipt=None):
        if ipt is None:
            return None
        jl.prompt_len = ipt.prompt_len()
        jl.before(query)
        size = f"{ipt.width}x{ipt.height}"
        response = openai.Image.create(
            model=self.model_id,
            prompt=query,
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
