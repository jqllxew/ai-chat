#### python 3.10

## 接入聊天
- ~~[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)（已不再维护）~~
- [OpenShamrock](https://github.com/whitechi73/OpenShamrock)（需要使用安卓环境）
#### 模拟器中安装
以下使用MuMu模拟器12，QQ 8.9.83
1. [Shizuku](https://github.com/RikkaApps/Shizuku)
2. [LSPatch](https://github.com/LSPosed/LSPatch)
3. [OpenShamrock](https://github.com/whitechi73/OpenShamrock)
4. qq

#### 使用 LSPatch（[原文档地址](https://whitechi73.github.io/OpenShamrock)）
- 打开 LSPatch 并在管理页面选择 + 新建修补，可以选择从存储目录选择QQAPK或者直接使用已经安装过的QQ
- 修补模式默认且应该优先选择本地模式，这样方便直接更新 Shamrock 模块而不用重新修补，缺点是需要 LSPatch 保持后台运行
- 其他配置保持默认，然后点击开始修补，修补完成后会提示安装(如果已经安装会提示卸载)
- 安装 Shamrock 模块后在管理页面点击修补好的 QQ 选择模块作用域 勾选上 Shamrock 模块然后保存
- 启动 Shamrock 并重新启动 QQ 客户端
- 此时 Shamrock 会显示已激活
#### 转发端口
```bash
# 确认模拟器adb调试端口
adb.exe connect 127.0.0.1:16384
# shamrock 主动http端口
adb.exe forward tcp:5700 tcp:5700
# 尝试ping通内网
adb.exe shell "ping 192.168.0.1"
# 不通就再转发回调端口
adb.exe forward tcp:7666 tcp:7666
```
#### 配置Shamrock
设置回调，如果能ping通内网就用内网ip，不能就用内部ip
```bash
# 确认模拟器内部ip
adb.exe shell "ifconfig"
```

## 图像生成
两种方式
#### 1，调用stable-diffusion-webui的接口
默认方式，前置条件: 搭建sd-webui
- 可以参考我的另一个项目[传送门](https://github.com/jqllxew/stable-diffusion-webui)
- 也可以通过[colab方式](https://colab.research.google.com/github/jqllxew/stable-diffusion-webui/blob/colab/fast_sd_A1111_colab.ipynb)
#### 2，使用diffusers库本地调用
~~可以去抱脸选择[支持diffusers库的模型](https://huggingface.co/models?library=diffusers)
推荐 [动漫风hakurei/waifu-diffusion](https://huggingface.co/hakurei/waifu-diffusion)
[2.5D风nuigurumi/basil_mix](https://huggingface.co/nuigurumi/basil_mix/tree/main)~~

## Demo
```bash
# python 3.10
pip install -r requirements_api.txt
python chat_demo.py
```