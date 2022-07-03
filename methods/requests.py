from methods.basetype import MethodBaseType
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
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        urllib3_cn.allowed_gai_family = Requests.family_v6 if type == 'AAAA' else Requests.family_v4
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
                if ip.startswith(start):
                    IPy.IP(ip)
                    return [ip]
                else:
                    return []
            except:
                continue
        return []
