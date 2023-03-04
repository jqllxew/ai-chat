

class BaseDict:
    def __init__(self):
        pass

    def to_dict(self, *ks, include=False):
        def judge(k, v):
            if v is None or callable(v):
                return False
            if include:
                return k in ks
            return k not in ks
        return {k: v for k, v in self.__dict__.items() if judge(k, v)}
