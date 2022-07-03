from methods.basetype import MethodBaseType
import psutil
import IPy


class Interface(MethodBaseType):
    @staticmethod
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        if type == 'A':
            name = 'AF_INET'
        else:
            name = 'AF_INET6'
        ips = []
        addr = psutil.net_if_addrs()
        for adapter in addr:
            if not interface or adapter == interface:
                for i in addr[adapter]:
                    if i.family.name == name:
                        address = i.address
                        try:
                            IPy.IP(address)
                            if address.startswith(start):
                                ips.append(address)
                        except:
                            continue
        return ips
