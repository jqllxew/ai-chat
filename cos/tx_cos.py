import logging

from qcloud_cos import CosS3Client, CosConfig, cos_client
from config import cos as cos_conf
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


def upload(key, binary_data):
    if client is None:
        logger.warn("[COS] cos客户端未被创建，图像将无法展示..")
        return ""
    response = client.put_object(
        Bucket=bucket,
        Body=binary_data,
        Key=key,
    )
    if response.get('ETag') is not None:
        return f"https://{bucket}.cos.{region}.myqcloud.com/{key}"
    return ""
