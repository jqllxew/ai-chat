import yaml


class ConfDict(dict):
    def __init__(self, data: dict, miss=False):
        super().__init__(data)
        self.data = data
        self.miss = miss

    def __getitem__(self, key):
        if key in self.data:
            val = self.data[key]
            if isinstance(val, dict) and not isinstance(val, ConfDict):
                self.data[key] = ConfDict(val)
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __missing__(self, key):
        val = ConfDict({}, True)
        self[key] = val
        return val


def display(_any):
    """
    用display判断配置文件参数，相当于把决定权留到最后
    :param _any: 任意参数
    :return:
    """
    if isinstance(_any, ConfDict) and _any.miss:
        return None
    else:
        return _any


with open("config.yaml", "r", encoding="utf-8") as file:
    yaml_string = file.read()
_data = yaml.load(yaml_string, Loader=yaml.FullLoader)
chat = ConfDict(_data.get('chat'))
qq = ConfDict(_data.get('qq'))
image = ConfDict(_data.get('image'))
cos = ConfDict(_data.get('cos'))
fanyi = ConfDict(_data.get('fanyi'))

if __name__ == "__main__":
    print(chat)
    print(qq)
    print(image)
    print(cos)
    print(fanyi)
