from methods.basetype import MethodBaseType
import requests
import IPy


class Requests(MethodBaseType):
    @staticmethod
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        if config and 'url' in config:
            urls = config['url'] if isinstance(config['url'], list) else [config['url']]
        else:
            v = '6' if type == 'AAAA' else '4'
            urls = [f'https://api{v}.ipify.org?format=json', f'https://v{v}.myip.la', f'https://api-ipv{v}.ip.sb/ip']
        for url in urls:
            try:
                ret = requests.get(url)
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
