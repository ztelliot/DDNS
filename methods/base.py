from type import IPInfo


class Method:
    @staticmethod
    def run(**kwargs) -> dict[str, IPInfo]:
        return {}

    @classmethod
    def getip(cls, **kwargs) -> dict[str, IPInfo]:
        return cls.run(**kwargs)
