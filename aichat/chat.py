
from collections import deque
from abc import ABC, abstractmethod

# 用户上下文存储 K=uid,V=deque
user_contexts: dict[int, deque] = {}
# 用户使用的模型
user_model_id: dict[int, str] = {}


class ChatAI(ABC):

    @abstractmethod
    def reply_text(self, uid: int, query: str) -> str:
        """
        :param uid: 标识对话用户id，比如qq号
        :param query: 用户发来的文本消息
        :return: reply content
        """
        raise NotImplementedError

    @abstractmethod
    def reply_image(self, uid: int, query: str, from_type: str) -> str:
        """
        :param uid: 标识对话用户id
        :param query: 用户发来的绘画要求
        :param from_type: 消息来源
        :return: reply image_path
        """
        raise NotImplementedError
