from methods.basetype import MethodBaseType
from methods.interface import Interface
from methods.api import API
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
import IPy
import jsonpath


class Requests(MethodBaseType):
    @staticmethod
    def family_v4():
        return socket.AF_INET

    @staticmethod
    def family_v6():
        return socket.AF_INET6

    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        ragf = urllib3_cn.allowed_gai_family
        urllib3_cn.allowed_gai_family = Requests.family_v6 if version == 6 else Requests.family_v4
        if interface:
            inips = Interface.getip(version, interface)
            if inips:
                rcc = urllib3_cn.create_connection

                def set_src(address, timeout, source_address=None, socket_options=None):
                    source_address = (inips[0], 0)
                    return rcc(address, timeout, source_address, socket_options)

                urllib3_cn.create_connection = set_src
            else:
                urllib3_cn.allowed_gai_family = ragf
                return []
        if kwargs.get("url"):
            apis = kwargs['url'] if isinstance(kwargs['url'], list) else [kwargs['url']]
        else:
            apis = API
        res = []
        for api in apis:
            addr = api["url"] if isinstance(api, dict) else api
            try:
                ret = requests.get(addr, timeout=3)
                ip = ''
                if isinstance(api, dict) and "key" in api:
                    ip = jsonpath.findall(api["key"], ret.json())
                    ip = ip[0] if ip else ''
                else:
                    ip = ret.text
                if ip and IPy.IP(ip).version() == version:
                    res = [ip]
                    break
            except:
                continue
        urllib3_cn.allowed_gai_family = ragf
        if interface and inips:
            urllib3_cn.create_connection = rcc
        return res
