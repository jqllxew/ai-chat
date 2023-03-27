from aichat import ChatGPT
from config import chat as chat_conf, display
from tts import speak


def _gpt():
    gpt35_conf = chat_conf['openai']['gpt3.5']
    return ChatGPT(
        uid="test_novel",
        api_key=display(gpt35_conf['api-key']),
        max_req_length=display(gpt35_conf['max-req-length']),
        max_resp_tokens=display(gpt35_conf['max-resp-tokens']),
        proxy=display(gpt35_conf['proxy']),
        from_type="test",
        need_ctx=False,
        need_ins=False)


def living(q: str, gpt: ChatGPT = None):
    gpt = gpt or _gpt()
    gpt.set_system("""
现在你是一个虚拟猫娘主播，你叫小白，18岁，喜欢在句子中与结尾加入"喵~"，你需要严格按照格式要求回复用户#
示例：
<speak voice="zhimiao_emo">
<emotion category="happy" intensity="1.0">我是小白，喵~</emotion>
</speak>
<emotion>标签可以包含文本
<break/>用于在文本中插入停顿
voice是固定参数你不需要改动
intensity是指定情绪强度。默认值为1.0,最小值为0.01。最大值为2.0。
你可选择的情感：
serious,sad,disgust,jealousy,embarrassed,happy,fear,surprise,neutral,frustrated,affectionate,gentle,angry,newscast,customer-service,story,living
接下来请按照格式回复
""")
    return gpt.reply_stream(q)


def translator(q: str, gpt: ChatGPT = None):
    gpt = gpt or _gpt()
    gpt.set_system("现在你是一个翻译者,你只需要翻译我的内容为汉语,请直接给出汉语翻译,不要说多余的解释。")
    return gpt.reply_stream(q)


if __name__ == "__main__":
    # res = translator("translator")
    res = living("你好主播")
    lines = ""
    for x in res:
        print(x or '\n', end='')
        lines += x
    speak(lines)
