from abc import ABC, abstractmethod


class ReplyAI(ABC):
    def __init__(self, uid, from_type, model_id=None):
        self.uid = uid
        self.from_type = from_type
        self.model_id = model_id

    @abstractmethod
    def generate(self, prompt):
        """
        :param prompt:
        :return: text or Iterator
        """
        raise NotImplementedError

    @abstractmethod
    def reply(self, query: str):
        """
        :param query: 文本消息
        :return: reply generate()
        """
        raise NotImplementedError
