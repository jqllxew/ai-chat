import json
from datetime import datetime, timedelta, timezone

import ai
from logger import logger
from plugin.byteplus import seedream, seedance


def get_current_time(val0=0, **kw) -> str:
    logger.info(f"调用获取时间: val=> {val0}")
    utc_offset = timedelta(hours=val0)
    utc_time = datetime.now(tz=timezone.utc) + utc_offset
    utc_time.timetz()
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


tool_map = {
    # "get_current_time": get_current_time,
    "seedream": seedream,
    "seedance": seedance
}
tools = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "get_current_time",
    #         "description": "根据utc获取当前时间",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "val0": {
    #                     "type": "number",
    #                     "description": "UTC偏移（以小时为单位）",
    #                 }
    #             },
    #             "required": ["val0"]
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "seedream",
            "description": "根据提示生成图像: (当用户需要画或者生成图像时需调用此方法)，可选择生成的图像大小(默认2K)，可选提供最多4张参考图像",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "生成图像的文本提示",
                    },
                    "size": {
                        "type": "string",
                        "description": "图像分辨率，可选 2K 或 4K",
                        "enum": ["2K", "4K"],
                        "default": "2K"
                    },
                    "img0": {
                        "type": "string",
                        "description": "参考图像 0（可选）"
                    },
                    "img1": {
                        "type": "string",
                        "description": "参考图像 1（可选）"
                    },
                    "img2": {
                        "type": "string",
                        "description": "参考图像 2（可选）"
                    },
                    "img3": {
                        "type": "string",
                        "description": "参考图像 3（可选）"
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "seedance",
            "description": "根据文本提示生成视频任务: (当用户需要生成视频时需调用此方法)，可选提供首帧与末帧图片作为过渡控制。函数会立即返回任务ID，后台会轮询完成后自动发送视频。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "视频生成的文本描述，例如场景、动作、氛围等"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "视频时长（单位：秒）。默认 5 秒，最高 12 秒"
                    },
                    "img0": {
                        "type": "string",
                        "description": "可选。首帧图片的 URL，用于控制视频起始画面"
                    },
                    "img1": {
                        "type": "string",
                        "description": "可选。末帧图片的 URL，用于控制视频结束画面"
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]
