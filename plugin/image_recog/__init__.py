import io
from urllib.request import urlopen
from alibabacloud_imagerecog20190930.client import Client as recog_client
from alibabacloud_imagerecog20190930.models import TaggingImageAdvanceRequest, RecognizeSceneAdvanceRequest
from alibabacloud_ocr20191230.client import Client as ocr_client
from alibabacloud_ocr20191230.models import RecognizeCharacterAdvanceRequest
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions
from config import plugin as plugin_conf

recog_conf = plugin_conf['image-recog']
access_key_id = recog_conf['aliyun']['access-key-id']
access_key_secret = recog_conf['aliyun']['access-key-secret']

recog_config = Config(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    endpoint='imagerecog.cn-shanghai.aliyuncs.com',
    region_id='cn-shanghai'
)
ocr_config = Config(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret,
    endpoint='ocr.cn-shanghai.aliyuncs.com',
    region_id='cn-shanghai'
)

def _recog(image_path, request, is_local=False):
    if is_local:
        # 场景一：文件在本地
        img = open(image_path, 'rb')
    else:
        # 场景二：使用任意可访问的url = 'https://viapi-test-bj.oss-cn-beijing.aliyuncs.com/viapi-3.0domepic/imagerecog/TaggingImage/TaggingImage1.jpg'
        img = io.BytesIO(urlopen(image_path).read())
    try:
        request.image_urlobject = img
        runtime = RuntimeOptions()
        # 初始化Client
        if isinstance(request, TaggingImageAdvanceRequest):
            client = recog_client(recog_config)
            response = client.tagging_image_advance(request, runtime)
        elif isinstance(request, RecognizeSceneAdvanceRequest):
            client = recog_client(recog_config)
            response = client.recognize_scene_advance(request, runtime)
        elif isinstance(request, RecognizeCharacterAdvanceRequest):
            client = ocr_client(ocr_config)
            request.output_probability = True
            request.min_height = 10
            response = client.recognize_character_advance(request, runtime)
        else:
            raise NotImplementedError(f'暂不支持{type(request).__name__}')
        # 获取整体结果
        body = response.body
        print(body)
        return body
    except Exception as e:
        # 获取整体报错信息
        print(e)
        return str(e)


def get_tag(image_path, is_local=False):
    body = _recog(image_path, TaggingImageAdvanceRequest(), is_local)
    return ','.join([f'{x.value}:{x.confidence}' for x in body.data.tags])


def get_scene(image_path, is_local=False):
    body = _recog(image_path, RecognizeSceneAdvanceRequest(), is_local)
    return ','.join([f'{x.value}:{x.confidence}' for x in body.data.tags])

def get_character(image_path, is_local=False):
    body = _recog(image_path, RecognizeCharacterAdvanceRequest(), is_local)
    return '\n'.join([x.text for x in body.data.results])

if __name__ == '__main__':
    print(get_character('https://checkimage.neea.cn/DCCA470BA1B4239AE8D342627CDEA789.jpg'))
    # response = requests.post('https://jlpt.neea.cn/book.do')
    # print(response.text)
