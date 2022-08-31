from methods.basetype import MethodBaseType
from methods.command import Command
import json
import IPy


class Curl(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", config: dict = None) -> list:
        command = f"curl -{version} -m 3 " + (f"--interface {interface} " if interface else '')
        if config and 'url' in config:
            urls = config['url'] if isinstance(config['url'], list) else [config['url']]
        else:
            urls = ['https://api.ipify.org?format=json', 'https://api.myip.la', 'https://api.ip.sb/ip']
        for url in urls:
            out = Command.run({'cmd': command + url, 'ssh': config['ssh'] if config and 'ssh' in config else {}})
            try:
                if out.startswith('{'):
                    ip = json.loads(out)['ip']
                else:
                    ip = out
                if ip and IPy.IP(ip).version() == version:
                    return [ip]
            except:
                continue
        return []
