from methods.basetype import MethodBaseType
from methods.command import Command
from methods.api import API
import json
import IPy
import jsonpath


class Curl(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        command = f"curl -{version} -m 10 " + (f"--interface {interface} " if interface else '')
        if kwargs.get("url"):
            apis = kwargs['url'] if isinstance(kwargs['url'], list) else [kwargs['url']]
        else:
            apis = API
        for api in apis:
            addr = api["url"] if isinstance(api, dict) else api
            out = Command.run(command=command + addr, ssh=kwargs.get("ssh"))
            try:
                ip = out
                if isinstance(api, dict) and "key" in api:
                    ip = jsonpath.findall(api["key"], json.loads(out))
                    ip = ip[0] if ip else ''
                if ip and IPy.IP(ip).version() == version:
                    return [ip]
            except:
                continue
        return []
