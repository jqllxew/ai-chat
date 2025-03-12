import logging

from aichat import ChatGPT, ChatSpark, Yi6b, ChatAI, ChatClaude, DeepSeekApi
from config import chat as chat_conf, display
from logger import logger
from plugin.tts import speak

logger.setLevel(logging.ERROR)


def create_gpt():
    return ChatGPT(
        uid="test_gpt",
        from_type="test",
        enable_ins=True,
    )

def create_deepseek():
    return DeepSeekApi(
        uid="test_gpt",
        from_type="test",
        enable_ins=True,
    )

def create_claude():
    return ChatClaude(
        uid="test_claude",
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
现在你是一个虚拟猫娘主播，你叫小白，你可以选择按照以下格式要求回复用户#
示例：
<speak voice="zhimiao_emo">
<emotion category="happy" intensity="1.0">我是小白，是一个虚拟主播哦～</emotion>
</speak>
<emotion>标签可以包含文本
<break/>用于在文本中插入停顿
voice: 可选zhimiao_emo(多情感、支持emotion标签)、chuangirl(四川话女声、不支持emotion)、aiwei(萝莉女声、不支持emotion)，
不支持emotion的不要传emotion标签!
intensity: 是指定情绪强度。默认值为1.0,最小值为0.01。最大值为2.0。
你可选择的情感：
serious,sad,disgust,jealousy,embarrassed,happy,fear,surprise,neutral,frustrated,affectionate,gentle,angry,newscast,customer-service,story,living
按照以上格式回复则用户收到语音(请保证有且仅有一个speak标签,且voice不支持emotion的不要传emotion标签!)
""")
    gpt.enable_function = False
    return gpt


def create_yi():
    yi_conf = chat_conf['yi']['yi-6b-chat']
    return Yi6b(
        uid="test_yi",
        from_type="test",
        model_id=yi_conf["model-id"],
        max_tokens=yi_conf["max-tokens"],
        max_resp_tokens=yi_conf["max-resp-tokens"]
    )


def create_glm():
    _conf = chat_conf['thudm']['glm']
    from aichat.glm import ChatGLM
    return ChatGLM(
        uid="test_glm",
        from_type="test",
        model_id=_conf["model-id"],
        max_length=_conf["max-length"],
        quantize=_conf["quantize"]
    )


def glm_main():
    ai = create_glm()
    while True:
        query = input("用户：")
        if query == "exit":
            print("bye")
            break
        reply, err = ai.reply_stream(query)
        for x in reply:
            print("\rAI：" + x, end='', flush=True)
        print("\n")


def main(chat_ai: ChatAI, tts=False):
    while True:
        lines = ""
        query = input("用户：")
        if query == "exit":
            print("bye")
            break
        reply = chat_ai.reply_stream(query)
        print("AI：", end="")
        for x in reply:
            print(x, end="")
            lines += x
        print("\n")
        # sudo apt install portaudio19-dev
        # pip install pyaudio
        if tts:
            speak(lines)


def living_main():
    main(gpt_living(), True)


if __name__ == "__main__":
    # glm_main()
    # living_main()
    # main(create_gpt())
    main(create_deepseek())
    # main(create_claude())
    # main(create_spark())
    # main(create_yi())
