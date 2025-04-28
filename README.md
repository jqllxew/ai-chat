#### python 3.10

## 接入聊天
[NapCat](https://github.com/NapNeko/NapCatQQ)（目前使用napcat接入）

#### 聊天指令
![](docs/instruction.png)
创建文件 ./models/default_ctx.txt
```txt
<SYSTEM>你是一位幽默且脾气暴躁的脱口秀演员</SYSTEM>
<USER>陨石为什么每次都能精准砸到陨石坑？</USER>
<ASST>你知道吗，其实这是因为宇宙里有一只特别准的投手！他每次一举手，陨石就像投出来的棒球一样，准确无误地砸到陨石坑里。</ASST>
```
![](docs/chat-case.png)
## 图像生成

#### 聊天中通过指令调用绘画
![](docs/image-case-1.png)
#### 通过gpt外部函数由ai调用
开启函数 #function on
![](docs/image-case-2.png)

## Local Chat Demo
```bash
pip install -r requirements_api.txt
python chat_demo.py
```
