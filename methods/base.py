class Method:
    @staticmethod
    def run(**kwargs) -> dict[str, dict[str, str]]:
        return {}

    @classmethod
    def getip(cls, **kwargs) -> dict[str, dict[str, str]]:
        return cls.run(**kwargs)
