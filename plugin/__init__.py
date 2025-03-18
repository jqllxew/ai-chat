import json
from datetime import datetime, timedelta, timezone

import ai
from plugin import speech_recog, image_recog
from logger import logger


def get_current_time(val0=0, c=...) -> str:
    utc_offset = timedelta(hours=val0)
    utc_time = datetime.now(tz=timezone.utc) + utc_offset
    utc_time.timetz()
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


def image_generate(val0, c: ai.base.ReplyAI):
    return ai.image.draw(c.uid, val0, c.from_type, use_template=False)


def mongo_query(val0, val1):
    from journal.mongo import db
    if db:
        q = json.loads(val1)
        logger.info(q)
        return db[val0].find(q)
    return "未配置数据库"


param = "val"
function_map = {
    "get_current_time": get_current_time,
    "image_generate": image_generate,
    # "get_image_tag": image_recog.get_tag,
    # "get_image_character": image_recog.get_character,
    # "get_speech_text": speech_recog.get_speech_text,
}
functions = [
    {
        "name": "get_current_time",
        "description": "根据utc获取当前时间",
        "parameters": {
            "type": "object",
            "properties": {
                param+"0": {
                    "type": "number",
                    "description": "UTC偏移（以小时为单位）",
                },
            }, "required": [param+"0"],
        }
    },
    {
        "name": "image_generate",
        "description": "传入prompt返回图像(可包含大小，例: 'a white siamese cat, 576x576')",
        "parameters": {
            "type": "object",
            "properties": {
                param+"0": {
                    "type": "string",
                    "description": "prompt,only use english",
                },
            }, "required": [param+"0"],
        }
    },
    # {
    #     "name": "get_image_tag",
    #     "description": "传入图片url获取图片打标信息，返回格式{标签:置信度}",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             param_name: {
    #                 "type": "string",
    #                 "description": "图片url",
    #             },
    #         }, "required": [param_name],
    #     }
    # },
    # {
    #     "name": "get_image_character",
    #     "description": "传入图片url获取图片中的文字内容",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             param_name: {
    #                 "type": "string",
    #                 "description": "图片url",
    #             },
    #         }, "required": [param_name],
    #     }
    # },
    # {
    #     "name": "get_speech_text",
    #     "description": "传入音频返回识别的文本信息",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             param_name: {
    #                 "type": "string",
    #                 "description": "语音文件(支持.mp3,.amr)路径",
    #             },
    #         }, "required": [param_name],
    #     }
    # },
]
