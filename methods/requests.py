from methods.basetype import MethodBaseType
from methods.interface import Interface
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
import IPy


class Requests(MethodBaseType):
    @staticmethod
    def family_v4():
        return socket.AF_INET

    @staticmethod
    def family_v6():
        return socket.AF_INET6

    @staticmethod
    def getip(version: int = 4, interface: str = "", config: dict = None) -> list:
        ragf = urllib3_cn.allowed_gai_family
        urllib3_cn.allowed_gai_family = Requests.family_v6 if version == 6 else Requests.family_v4
        if interface:
            inips = Interface.getip(version, interface)
            if inips:
                rcc = urllib3_cn.create_connection
                def set_src(address, timeout, source_address = None, socket_options = None):
                    source_address = (inips[0], 0)
                    return rcc(address, timeout, source_address, socket_options)
                urllib3_cn.create_connection = set_src
            else:
                urllib3_cn.allowed_gai_family = ragf
                return []
        if config and 'url' in config:
            urls = config['url'] if isinstance(config['url'], list) else [config['url']]
        else:
            urls = ['https://api.ipify.org?format=json', 'https://api.myip.la', 'https://api.ip.sb/ip']
        res = []
        for url in urls:
            try:
                ret = requests.get(url, timeout=3)
                try:
                    ip = ret.json()['ip']
                except:
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
