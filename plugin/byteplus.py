import base64
import threading
import time
from io import BytesIO

import httpx
import requests
from PIL.Image import Image
from openai import OpenAI

from config import chat as conf, display
from logger import logger
from plugin import tx_cos, tos
from plugin.reply import send_private, send_group, send

API_KEY = display(conf["byteplus"]["doubao"]["api-key"])
client = OpenAI(
    base_url=display(conf["byteplus"]["doubao"]["base-url"]),
    api_key=API_KEY, http_client=httpx.Client(proxy="http://127.0.0.1:7897")
)
VIDEO_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"


def download_for_proxy(url: str) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers, proxies={
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"}, timeout=20)
    resp.raise_for_status()  # 下载失败会抛异常
    return resp.content


def seedream(prompt: str, size="2K", img0=None, img1=None, img2=None, img3=None, **kw):
    extra_body = {
        "watermark": False,
        "sequential_image_generation": "disabled"
    }
    images = []
    for x in [img0, img1, img2, img3]:
        if x:
            images.append(x)
    if images:
       extra_body.update({
           "image": images
       })
    res = client.images.generate(
        model="ep-20260214224039-jvj5l",
        # model="ep-20260224181306-h8s72",
        prompt=prompt,
        size=size,
        response_format="url",
        extra_body=extra_body
    )
    image_url = res.data[0].url
    logger.info(f"seedream image url: {image_url}")
    b_content = download_for_proxy(image_url)
    b64_str = base64.b64encode(b_content).decode("utf-8")
    send(kw.get("_self"), f"[CQ:image,file=base64://{b64_str}]")
    tos_url = tos.upload(b_content, "jpg", "aichat", check=False)
    return (f"success! pic url is {tos_url}. "
            f"(The pictures have been sent in advance and do not need to be sent again. "
            f"This reply is only for your reference in the future.)")


def seedance(prompt, duration=5, img0=None, img1=None, **kw):
    content = [{
        "type": "text",
        "text": prompt
    }]
    payload = {
        "model": "ep-20260214230505-l9hl7",
        "generate_audio": True,
        "ratio": "adaptive",
        "duration": duration,
        "watermark": False
    }
    if img0:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": img0
            },
            "role": "first_frame"
        })
    if img1:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": img1
            },
            "role": "last_frame"
        })
    payload.update({"content": content})
    response = requests.post(VIDEO_BASE_URL, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }, proxies={
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"
    }, json=payload)
    response.raise_for_status()
    res_data = response.json()
    logger.info(f"seedance res: {res_data}")
    task_id = res_data["id"]
    _self = kw.get("_self")
    # 启动后台轮询线程
    threading.Thread(
        target=_poll_task_status,
        args=(task_id, _self,),
        daemon=True
    ).start()
    return "Your video is being generated. It will be automatically sent shortly."


def _poll_task_status(task_id, that):
    """
    后台轮询，不影响主线程返回
    """
    while True:
        try:
            result = get_video_result(task_id)
            if result and result.get("status") == "succeeded":
                video_url = result["content"]["video_url"]
                send(that, f"[CQ:video,file={video_url}]")
                break
        except Exception as e:
            logger.error(f"video task err: \n{e}")
        time.sleep(5)  # 每5秒查询一次


def get_video_result(task_id):
    url = f"{VIDEO_BASE_URL}/{task_id}"
    response = requests.get(url, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }, proxies={
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"
    })
    response.raise_for_status()
    data = response.json()
    logger.info(f"video task{task_id}: {data}")
    return data
