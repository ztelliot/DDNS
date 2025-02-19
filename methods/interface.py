import psutil
from methods.base import Method
from type import IPInfo


class Interface(Method):
    @staticmethod
    def run(version: int = None, interface: str = None) -> dict[str, IPInfo]:
        name = ('AF_INET' if version == 4 else 'AF_INET6') if version else None
        ips = {}
        addr = psutil.net_if_addrs()
        for adapter in addr:
            if not interface or adapter == interface:
                for i in addr[adapter]:
                    if (not name and i.family.name.startswith("AF_INET")) or i.family.name == name:
                        if i.address:
                            ips[i.address] = IPInfo(interface=adapter)
        return ips
