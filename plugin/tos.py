import hashlib
from io import BytesIO
from typing import Union

import requests
import tos
from PIL.Image import Image

from config import tos as tos_conf
from logger import logger

_endpoint = tos_conf['endpoint']
_bucket = tos_conf['bucket']
_client = tos.TosClientV2(
    ak=tos_conf['ak'],
    sk=tos_conf['sk'],
    endpoint=_endpoint,
    region=tos_conf['region'],
    proxy_host="127.0.0.1",
    proxy_port=7897
)


def upload(data: Union[str, bytes], suffix: str, prefix="other", check=True):
    pre_url = f"https://{_bucket}.{_endpoint}"
    buffer = BytesIO()
    if isinstance(data, str):
        if pre_url in data:
            return data
        _resp = requests.get(data, timeout=20)
        buffer.write(_resp.content)
    # 图片类型
    elif isinstance(data, Image):
        data.save(buffer, format="jpeg")
    # bytes 类型（比如 requests.post 返回的 resp.content）
    elif isinstance(data, (bytes, bytearray)):
        buffer.write(data)
    # 其他类型可以继续扩展
    else:
        raise RuntimeError(f"未知上传类型: {type(data)}")
    content = buffer.getvalue()
    # 计算 md5
    md5_hash = hashlib.md5(content).hexdigest()
    object_key = f"{prefix}/{md5_hash}.{suffix}"
    tos_url = f"{pre_url}/{object_key}"
    if check:
        try: # 检查是否存在
            _client.head_object(bucket=_bucket, key=object_key)
            return tos_url
        except Exception:
            pass  # 不存在才上传
    resp = _client.put_object(
        bucket=_bucket,
        key=object_key,
        content=content,
    )
    if resp.status_code != 200:
        raise Exception(f"Tos Upload failed: {resp.status_code}, resp: {resp}")
    logger.info(f"tos url: {tos_url}")
    return tos_url
