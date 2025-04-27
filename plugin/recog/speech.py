import json
import os
import time

from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from config import plugin as plugin_conf
from plugin import tx_cos

recog_conf = plugin_conf['speech-recog']
recog_voices_path = recog_conf['voices-base-path']
access_key_id = recog_conf['aliyun']['access-key-id']
access_key_secret = recog_conf['aliyun']['access-key-secret']
app_key = recog_conf['aliyun']['app-key']
# 地域ID，固定值。
REGION_ID = "cn-shanghai"
PRODUCT = "nls-filetrans"
DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
API_VERSION = "2018-08-17"
POST_REQUEST_ACTION = "SubmitTask"
GET_REQUEST_ACTION = "GetTaskResult"
# 请求参数
KEY_APP_KEY = "appkey"
KEY_FILE_LINK = "file_link"
KEY_VERSION = "version"
KEY_ENABLE_WORDS = "enable_words"
# 是否开启智能分轨
KEY_AUTO_SPLIT = "auto_split"
# 响应参数
KEY_TASK = "Task"
KEY_TASK_ID = "TaskId"
KEY_STATUS_TEXT = "StatusText"
KEY_RESULT = "Result"
# 状态值
STATUS_SUCCESS = "SUCCESS"
STATUS_RUNNING = "RUNNING"
STATUS_QUEUEING = "QUEUEING"


def _upload(local_path):
    if not os.path.exists(recog_voices_path):
        return None
    with open(recog_voices_path+local_path, mode='rb') as f:
        _voice = f.read()
        store_dir = tx_cos.store_dir('voices')
        return tx_cos.upload(f"{store_dir}/{local_path}", _voice)


def get_speech_text(local_path=None, file_path=None, c=None):
    if local_path:
        file_path = _upload(local_path)
    if not file_path:
        return ""
    # 创建AcsClient实例
    client = AcsClient(access_key_id, access_key_secret, REGION_ID)
    # 提交录音文件识别请求
    postRequest = CommonRequest()
    postRequest.set_domain(DOMAIN)
    postRequest.set_version(API_VERSION)
    postRequest.set_product(PRODUCT)
    postRequest.set_action_name(POST_REQUEST_ACTION)
    postRequest.set_method('POST')
    # 新接入请使用4.0版本，已接入（默认2.0）如需维持现状，请注释掉该参数设置。
    # 设置是否输出词信息，默认为false，开启时需要设置version为4.0。
    task = {KEY_APP_KEY : app_key, KEY_FILE_LINK : file_path, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False}
    # 开启智能分轨，如果开启智能分轨，task中设置KEY_AUTO_SPLIT为True。
    # task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False, KEY_AUTO_SPLIT : True}
    task = json.dumps(task)
    postRequest.add_body_params(KEY_TASK, task)
    taskId = ""
    try:
        postResponse = client.do_action_with_exception(postRequest)
        postResponse = json.loads(postResponse)
        statusText = postResponse[KEY_STATUS_TEXT]
        if statusText == STATUS_SUCCESS :
            print("录音文件识别请求成功响应！")
            taskId = postResponse[KEY_TASK_ID]
        else :
            print("录音文件识别请求失败！")
            return
    except ServerException as e:
        print(e)
    except ClientException as e:
        print(e)
    # 创建CommonRequest，设置任务ID。
    getRequest = CommonRequest()
    getRequest.set_domain(DOMAIN)
    getRequest.set_version(API_VERSION)
    getRequest.set_product(PRODUCT)
    getRequest.set_action_name(GET_REQUEST_ACTION)
    getRequest.set_method('GET')
    getRequest.add_query_param(KEY_TASK_ID, taskId)
    # 提交录音文件识别结果查询请求
    # 以轮询的方式进行识别结果的查询，直到服务端返回的状态描述符为"SUCCESS"、"SUCCESS_WITH_NO_VALID_FRAGMENT"，
    # 或者为错误描述，则结束轮询。
    while True :
        try :
            getResponse = client.do_action_with_exception(getRequest)
            getResponse = json.loads(getResponse)
            statusText = getResponse[KEY_STATUS_TEXT]
            if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING :
                # 继续轮询
                time.sleep(10)
            else :
                # 退出轮询
                break
        except ServerException as e:
            print(e)
        except ClientException as e:
            print(e)
    if statusText == STATUS_SUCCESS:
        print("录音文件识别成功！")
        return getResponse[KEY_RESULT]['Sentences'][0]['Text']
    else:
        return ""


if __name__ == "__main__":
    fileLink = "https://gw.alipayobjects.com/os/bmw-prod/0574ee2e-f494-45a5-820f-63aee583045a.wav"
    # 执行录音文件识别
    res = get_speech_text(file_path=fileLink)
    print(res)