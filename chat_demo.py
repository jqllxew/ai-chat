import logging
from aichat import ChatGPT, ChatSpark
from config import chat as chat_conf, display
from plugin.tts import speak
from logger import logger

logger.setLevel(logging.ERROR)


def create_gpt():
    gpt_conf = chat_conf['openai']['gpt']
    return ChatGPT(
        uid="test_gpt",
        api_key=display(gpt_conf['api-key']),
        proxy=display(gpt_conf['proxy']),
        from_type="test",
        enable_ins=True,
    )


def create_spark():
    spark_conf = chat_conf['iflytek']['spark']
    return ChatSpark(
        uid="test_spark",
        app_id=display(spark_conf['app-id']),
        api_key=display(spark_conf['api-key']),
        api_secret=display(spark_conf['api-secret']),
        from_type="test",
        enable_ins=False,
    )


def gpt_living(gpt: ChatGPT = None) -> ChatGPT:
    gpt = gpt or create_gpt()
    # 需要阿里云tts
    gpt.set_system("""
现在你是一个虚拟猫娘主播，你叫小白，可以适当在句子中或结尾加入"喵~"，你可以选择按照以下格式要求回复用户#
示例：
<speak voice="zhimiao_emo">
<emotion category="happy" intensity="1.0">我是小白，喵~</emotion>
</speak>
<emotion>标签可以包含文本
<break/>用于在文本中插入停顿
voice可选zhimiao_emo(多情感、支持emotion标签)、chuangirl(四川话女声、不支持emotion)、aiwei(萝莉女声、不支持emotion)
intensity是指定情绪强度。默认值为1.0,最小值为0.01。最大值为2.0。
你可选择的情感：
serious,sad,disgust,jealousy,embarrassed,happy,fear,surprise,neutral,frustrated,affectionate,gentle,angry,newscast,customer-service,story,living
按照以上格式回复则用户收到语音(请保证有且仅有一个speak标签)
""")
    gpt.enable_function = False
    return gpt


if __name__ == "__main__":
    ai = gpt_living()
    # ai = create_gpt()
    # ai = create_spark()
    while True:
        lines = ""
        query = input("用户：")
        if query == "exit":
            print("bye")
            break
        print("AI：", end="")
        reply = ai.reply_stream(query)
        for x in reply:
            print(x, end="")
            lines += x
        print("\n")
        # sudo apt install portaudio19-dev
        # pip install pyaudio
        # speak(lines)
