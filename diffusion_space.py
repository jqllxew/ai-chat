import re

import gradio as gr
import torch

from fanyi import youdao
from aiimage.diffusers import prefix_prompt, inference
from config import image as image_conf, display
from logger import logger

model_id = display(image_conf['diffusers']['model-id'])


def _inference(_prompt, _guidance, _steps, _width, _height, _seed, _image, _strength, _neg_prompt, _auto_prefix):
    if model_id is None:
        return None, "Error 你还未配置本地模型"
    pattern = '[\u4e00-\u9fa5]+'
    if re.search(pattern, _prompt):
        logger.debug(f"提示：{_prompt}")
        _prompt = youdao.chs2en(_prompt)
    if re.search(pattern, _neg_prompt):
        logger.debug(f"负提示：{_neg_prompt}")
        _neg_prompt = youdao.chs2en(_neg_prompt)
    return inference(prompt=_prompt,
                     guidance=_guidance,
                     steps=_steps,
                     width=_width,
                     height=_height,
                     seed=_seed,
                     img=_image,
                     strength=_strength,
                     neg_prompt=_neg_prompt,
                     auto_prefix=_auto_prefix)


css = """
.main-div div{display:inline-flex;align-items:center;gap:.8rem;font-size:1.75rem}
.main-div div h1{font-weight:900;margin-bottom:7px}
.main-div p{margin-bottom:10px;font-size:94%}
a{text-decoration:underline}
.tabs{margin-top:0;margin-bottom:0}
#gallery{min-height:20rem}
"""
if __name__ == "__main__":
    with gr.Blocks(css=css) as demo:
        gr.HTML(
            f"""
                <div class="main-div">
                  <div>
                    <h1>{ model_id if model_id is not None else "未配置本地模型" }</h1>
                  </div>
                  <p>
                   Demo for Stable Diffusion model.<br>
                  </p>
                  Running on {"<b>GPU 🔥</b>" if torch.cuda.is_available() else f"<b>CPU 🥶</b>"}<br><br>
                </div>
            """
        )
        with gr.Row():
            with gr.Column(scale=55):
                with gr.Group():
                    with gr.Row():
                        prompt = gr.Textbox(label="Prompt", show_label=False, max_lines=2,
                                            placeholder=f"{prefix_prompt} [Your prompt]").style(container=False)
                        generate = gr.Button(value="Generate")  # .style(rounded=(False, True, True, False))
                    image_out = gr.Image()
                error_output = gr.Markdown()

            with gr.Column(scale=45):
                with gr.Tab("Options"):
                    with gr.Group():
                        neg_prompt = gr.Textbox(label="Negative prompt", placeholder="What to exclude from the image")
                        auto_prefix = gr.Checkbox(label="Prefix styling tokens automatically ()", value=prefix_prompt,
                                                  visible=prefix_prompt)
                        with gr.Row():
                            guidance = gr.Slider(label="Guidance scale", value=7.5, maximum=15)
                            steps = gr.Slider(label="Steps", value=26, minimum=2, maximum=75, step=1)

                        with gr.Row():
                            width = gr.Slider(label="Width", value=768, minimum=64, maximum=1024, step=8)
                            height = gr.Slider(label="Height", value=768, minimum=64, maximum=1024, step=8)

                        seed = gr.Slider(0, 2147483647, label='Seed (0 = random)', value=0, step=1)

                with gr.Tab("Image to image"):
                    with gr.Group():
                        image = gr.Image(label="Image", tool="editor", type="pil")
                        strength = gr.Slider(label="Transformation strength", minimum=0, maximum=1, step=0.01,
                                             value=0.5)

        auto_prefix.change(lambda x: gr.update(placeholder=f"{prefix_prompt} [Your prompt]" if x else "[Your prompt]"),
                           inputs=auto_prefix, outputs=prompt, queue=False)

        inputs = [prompt, guidance, steps, width, height, seed, image, strength, neg_prompt, auto_prefix]
        outputs = [image_out, error_output]
        prompt.submit(_inference, inputs=inputs, outputs=outputs)
        generate.click(_inference, inputs=inputs, outputs=outputs)

        gr.HTML("""
        <div style="border-top: 1px solid #303030;">
          <br>
          <p>This space was created using <a href="https://huggingface.co/spaces/anzorq/sd-space-creator">SD Space Creator</a>.</p>
        </div>
        """)
    demo.queue(concurrency_count=1)
    demo.launch(share=False)
