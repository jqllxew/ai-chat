from datetime import datetime, timedelta, timezone

from plugin import image_recog


def get_current_time(val0=0) -> str:
    utc_offset = timedelta(hours=val0)
    utc_time = datetime.now(tz=timezone.utc) + utc_offset
    utc_time.timetz()
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


class GptFunction:

    param_name = "val0"
    function_map = {
        "get_current_time": get_current_time,
        "get_image_tag": image_recog.get_tag,
        "get_image_character": image_recog.get_character
    }
    functions = [
        {
            "name": "get_current_time",
            "description": "根据utc获取当前时间",
            "parameters": {
                "type": "object",
                "properties": {
                    param_name: {
                        "type": "number",
                        "description": "UTC偏移（以小时为单位）",
                    },
                },
                "required": [param_name],
            }
        },
        {
            "name": "get_image_tag",
            "description": "传入图片url获取图片打标信息，返回格式{标签:置信度}",
            "parameters": {
                "type": "object",
                "properties": {
                    param_name: {
                        "type": "string",
                        "description": "图片url",
                    },
                },
                "required": [param_name],
            }
        },
        {
            "name": "get_image_character",
            "description": "传入图片url获取图片中的文字内容",
            "parameters": {
                "type": "object",
                "properties": {
                    param_name: {
                        "type": "string",
                        "description": "图片url",
                    },
                },
                "required": [param_name],
            }
        }
    ]


__all__ = ["GptFunction"]
