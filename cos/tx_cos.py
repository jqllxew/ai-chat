import time
from qcloud_cos import CosS3Client, CosConfig
from config import cos as cos_conf

# import sys
# import logging
# logging.basicConfig(level=logging.INFO, stream=sys.stdout)
tx_cos_conf = cos_conf['tx']
secret_id = tx_cos_conf['secret-id']
secret_key = tx_cos_conf['secret-key']
region = tx_cos_conf['region']
bucket = tx_cos_conf['bucket']
token = None  # 使用临时密钥需要传入 Token，默认为空，可不填
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)
client = CosS3Client(config)  # 获取客户端对象


def upload(key, binary_data):
    response = client.put_object(
        Bucket=bucket,
        Body=binary_data,
        Key=key,
    )
    if response.get('ETag') is not None:
        return f"https://{bucket}.cos.{region}.myqcloud.com/{key}"
    return ""


if __name__ == "__main__":
    # binary_data = open('../models/_generator/xx.png', 'rb')
    print(upload(f"test/{int(time.time_ns())}.png",
                 open('../models/_generator/xx.png', 'rb')))
