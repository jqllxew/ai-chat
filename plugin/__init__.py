import json
from datetime import datetime, timedelta, timezone

import ai
from logger import logger


def get_current_time(val0=0, c=...) -> str:
    logger.info(f"调用获取时间: val=> {val0}")
    utc_offset = timedelta(hours=val0)
    utc_time = datetime.now(tz=timezone.utc) + utc_offset
    utc_time.timetz()
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


# def image_generate(val0, c: ai.base.ReplyAI):
#     return ai.image.draw(c.uid, val0, c.from_type, use_template=False)


def mongo_query(val0, val1):
    from journal.mongo import db
    if db:
        q = json.loads(val1)
        logger.info(q)
        return db[val0].find(q)
    return "未配置数据库"


param = "val"
tool_map = {
    "get_current_time": get_current_time,
}
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "根据utc获取当前时间",
            "parameters": {
                "type": "object",
                "properties": {
                    param + "0": {
                        "type": "number",
                        "description": "UTC偏移（以小时为单位）",
                    }
                },
                "required": [param + "0"]
            }
        }
    }
]
