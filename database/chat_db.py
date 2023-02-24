from abc import ABC, abstractmethod


class ChatDB(ABC):

    def __init__(self, origin, from_type):
        pass

    @abstractmethod
    async def before(self, uid, model_id, query, prompt):
        raise NotImplementedError

    @abstractmethod
    async def after(self, uid, model_id, res_text):
        raise NotImplementedError

    @abstractmethod
    async def error(self, uid, e):
        raise NotImplementedError
