from methods.basetype import MethodBaseType
from methods.command import Command
import platform
import IPy


class Interface(MethodBaseType):
    @staticmethod
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        sys = platform.system()
        if sys == "Windows":
            return []
        if type == "A":
            command = "ip -4 addr show "
        elif type == "AAAA":
            command = "ip -6 addr show "
        else:
            command = "ip addr show "
        if interface:
            command += interface
        out = Command.run({'cmd': command, 'ssh': config['ssh'] if config and 'ssh' in config else {}})
        ips = []
        for line in out.split('\n'):
            if line.strip().startswith("inet"):
                ip = line.strip().split()[1].split("/")[0]
                try:
                    IPy.IP(ip)
                    if ip.startswith(start):
                        ips.append(ip)
                        continue
                        # break  # only select the first ip
                except:
                    continue
        return ips
