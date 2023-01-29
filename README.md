

# 项目结构与说明
```
aichat/ #对话ai调用
aiimage/  #图像生成调用
cos/    #对象存储
fanyi/  #文本翻译
route/  #路由提供接口（比如提供给go-cqhttp转发消息）
diffusion_space.py  #扩散模型图像生成demo
config_example.yaml #配置文件示例
main.py
```
#### 接入qq需使用 gocqhttp 配置到启动端口，参考：[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

# cuda 对应 pytorch 版本安装
```
pip3 install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu117 --proxy=xx
```
#### 自己具体的环境请参考：[Pytorch](https://pytorch.org/get-started/locally/)

# 关于解决 NSFW 问题
#### diffusers库的 Pipeline调用模型生成通常会有这样的警告
```
Potential NSFW content was detected in one or more images. A black image will be returned instead.
Try again with a different prompt and/or seed.
```
#### 可以对该检测文件直接进行修改
```
venv/Lib/site-packages/diffusers/pipelines/stable_diffusion/safety_checker.py
```
#### 如下两个方法中
```
@torch.no_grad()
def forward(self, clip_input, images):
...
# has_nsfw_concepts = [len(res["bad_concepts"]) > 0 for res in result] # 设置为空数组
has_nsfw_concepts = []
...
```
```
@torch.no_grad()
def forward_onnx(self, clip_input: torch.FloatTensor, images: torch.FloatTensor):
...
# images[has_nsfw_concepts] = 0.0  # black image 注释掉这里

return images, has_nsfw_concepts
```
