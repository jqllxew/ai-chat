#### python 3.10

## 接入聊天
- qq [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
- 微信 [simple-wechaty](https://github.com/jqllxew/simple-wechaty)

## 图像生成
两种方式
#### 1，调用stable-diffusion-webui的接口
默认方式，前置条件: 搭建sd-webui
- 可以参考我的另一个项目[传送门](https://github.com/jqllxew/stable-diffusion-webui)
- 也可以通过[colab方式](https://colab.research.google.com/github/jqllxew/stable-diffusion-webui/blob/colab/fast_sd_A1111_colab.ipynb)
#### 2，使用diffusers库本地调用
可以去抱脸选择[支持diffusers库的模型](https://huggingface.co/models?library=diffusers) \
推荐 [动漫风hakurei/waifu-diffusion](https://huggingface.co/hakurei/waifu-diffusion)
[2.5D风nuigurumi/basil_mix](https://huggingface.co/nuigurumi/basil_mix/tree/main)
