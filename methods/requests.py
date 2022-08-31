from methods.basetype import MethodBaseType
from methods.interface import Interface
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
import IPy


class Requests(MethodBaseType):
    @staticmethod
    def family_v4():
        family = socket.AF_INET
        return family

    @staticmethod
    def family_v6():
        family = socket.AF_INET6
        return family

    @staticmethod
    def getip(version: int = 4, interface: str = "", config: dict = None) -> list:
        urllib3_cn.allowed_gai_family = Requests.family_v6 if version == 6 else Requests.family_v4
        if interface:
            inips = Interface.getip(version, interface)
            if inips:
                rcc = requests.packages.urllib3.util.connection.create_connection
                def set_src_addr(address, timeout, *args, **kw):
                    source_address = (inips[0], 0)
                    return rcc(address, timeout=timeout, source_address=source_address)
                urllib3_cn.create_connection = set_src_addr
            else:
                return []
        if config and 'url' in config:
            urls = config['url'] if isinstance(config['url'], list) else [config['url']]
        else:
            urls = ['https://api.ipify.org?format=json', 'https://api.myip.la', 'https://api.ip.sb/ip']
        for url in urls:
            try:
                ret = requests.get(url, timeout=3)
                try:
                    ip = ret.json()['ip']
                except:
                    ip = ret.text
                if ip and IPy.IP(ip).version() == version:
                    return [ip]
                else:
                    return []
            except:
                continue
        return []
