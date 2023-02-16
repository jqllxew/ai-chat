
from collections import deque
from collections.abc import Iterator
from abc import ABC, abstractmethod
import aiimage

# 用户上下文存储 K=uid,V=deque
user_contexts: dict[str, deque] = {}
# 用户使用的模型
user_model_id: dict[str, str] = {}


class ChatAI(ABC):

    def get_prompt_by_uid(self, uid: str, query="", sep="\r\n") -> str:
        """
        :param uid: 标识对话用户id，比如qq号
        :param query: 用户发来的文本消息
        :param sep: 分隔符
        :return: 上下文
        """
        if user_contexts.get(uid) is None:
            user_contexts[uid] = deque()
        if query:
            user_contexts[uid].append(query)
        return sep.join(user_contexts[uid])

    @abstractmethod
    def reply_text(self, uid: str, query: str) -> str:
        """
        :param uid: 标识对话用户id
        :param query: 用户发来的文本消息
        :return: reply content
        """
        raise NotImplementedError

    @abstractmethod
    def reply_stream(self, uid: str, query: str) -> Iterator[str]:
        """
        :param uid: 标识对话用户id
        :param query: 用户发来的文本消息
        :return: reply 生成器文本
        """
        raise NotImplementedError

    def reply_image(self, uid: str, query: str, from_type: str) -> str:
        """
        :param uid: 标识对话用户id
        :param query: 用户发来的绘画要求
        :param from_type: 消息来源
        :return: reply image_path
        """
        image_res = aiimage.generate(uid, query, from_type)
        reply_format = "提示词：{}\n负提示：{}\n随机数：{}\n耗时秒：{:.3f}\n宽高：{}\n".format(
            image_res.prompt if image_res.image is None else (image_res.prompt + '+[图片参数]'),
            "默认" if image_res.neg_prompt == "" else image_res.neg_prompt,
            image_res.seed, image_res.generate_seconds, f"{image_res.width}x{image_res.height}")
        if image_res.generate_err is None:
            if from_type == 'qq':
                reply_format += f"[CQ:image,file={image_res.generate_image_path}]"
            elif from_type == 'wx':
                reply_format += f"[image={image_res.generate_image_path}]"
            else:
                reply_format += image_res.generate_image_path
        else:
            reply_format += f"generate error because {image_res.generate_err}"
        return reply_format
