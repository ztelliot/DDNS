from methods.basetype import MethodBaseType
import psutil
import IPy


class Interface(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        name = 'AF_INET' if version == 4 else 'AF_INET6'
        ips = []
        addr = psutil.net_if_addrs()
        for adapter in addr:
            if not interface or adapter == interface:
                for i in addr[adapter]:
                    if i.family.name == name:
                        address = i.address
                        try:
                            if address and IPy.IP(address).version() == version:
                                ips.append(address)
                        except:
                            continue
        return ips
