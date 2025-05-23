import logging
from datetime import datetime
from io import BytesIO

import PIL
from PIL import Image
from qcloud_cos import CosS3Client, CosConfig, cos_client
from config import cos as cos_conf, display
from logger import logger

cos_client.logger.setLevel(logging.WARN)
tx_cos_conf = cos_conf['tx']
secret_id = tx_cos_conf['secret-id']
secret_key = tx_cos_conf['secret-key']
region = tx_cos_conf['region']
bucket = tx_cos_conf['bucket']


def __create():
    try:
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        return CosS3Client(config)
    except Exception as e:
        logger.warn(f"[COS] err: {e}")
        return None


client = __create()


def store_dir(res_type):
    template = display(cos_conf['tx']['store-dir'])
    if template:
        try:
            return template.format(type=res_type, date=datetime.utcnow().strftime('%Y%m%d'))
        except Exception as e:
            logger.error(f"[COS] store-dir模板错误\nerr: {e}")
    return ""


def upload(key, data):
    if not client:
        raise RuntimeError("[COS] cos客户端未被创建..")
    if isinstance(data, str):
        return data
    buffer = BytesIO()
    if isinstance(data, PIL.Image.Image):
        data.save(buffer, format="jpeg")
    else:
        raise RuntimeError("未知上传类型")
    response = client.put_object(
        Bucket=bucket,
        Body=buffer.getvalue(),
        Key=key,
    )
    if response.get('ETag'):
        return f"https://{bucket}.cos.{region}.myqcloud.com/{key}"
    return ""


def tmp_sts(duration_seconds) -> dict:
    """
    set PYTHONUTF8=1
    pip install qcloud-python-sts
    :return:
    """
    from sts.sts import Sts
    config = {
        # 请求URL，域名部分必须和domain保持一致
        # 使用外网域名时：https://sts.tencentcloudapi.com/
        # 使用内网域名时：https://sts.internal.tencentcloudapi.com/
        'url': 'https://sts.tencentcloudapi.com/',
        'domain': 'sts.tencentcloudapi.com',
        'duration_seconds': duration_seconds,
        'secret_id': secret_id,
        'secret_key': secret_key,
        'bucket': bucket,
        'region': region,
        'allow_prefix': ['*'],
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            'name/cos:PostObject',
            # 分片上传
            'name/cos:InitiateMultipartUpload',
            'name/cos:ListMultipartUploads',
            'name/cos:ListParts',
            'name/cos:UploadPart',
            'name/cos:CompleteMultipartUpload'
        ],
    }
    try:
        sts = Sts(config)
        return dict(sts.get_credential())
    except Exception as e:
        logger.warn(f"[COS] err: {e}")
