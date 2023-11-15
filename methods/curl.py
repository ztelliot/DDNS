from methods.basetype import MethodBaseType
from methods.command import Command
from methods.getip import API
import json
import IPy


class Curl(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", config: dict = None) -> list:
        command = f"curl -{version} -m 10 " + (f"--interface {interface} " if interface else '')
        if config and 'url' in config:
            urls = config['url'] if isinstance(config['url'], list) else [config['url']]
        else:
            urls = API
        for url in urls:
            addr = url
            if isinstance(url, dict):
                addr = url["url"]
            out = Command.run({'cmd': command + addr, 'ssh': config['ssh'] if config and 'ssh' in config else {}})
            try:
                ip = ''
                if "key" in url:
                    if url["key"] == "cloudflare":
                        for i in out.split('\n'):
                            if i.startswith("ip="):
                                ip = i.lstrip("ip=")
                                break
                    else:
                        ip = json.loads(out)
                        for i in url["key"].split('.'):
                            ip = ip[i]
                else:
                    try:
                        ip = json.loads(out)['ip']
                    except:
                        ip = out
                if ip and IPy.IP(ip).version() == version:
                    return [ip]
            except:
                continue
        return []
