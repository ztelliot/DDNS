from methods.basetype import MethodBaseType
from methods.command import Command
import IPy
import urllib3
import requests
from requests.auth import HTTPBasicAuth
from librouteros import connect
from librouteros.query import Key

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RouterOSSSH(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        if not kwargs:
            return []
        command = "/ipv6 " if version == 6 else "/ip "
        command += "address print "
        if interface:
            command += "where interface=" + interface
        out = Command.run(command=command, ssh=kwargs)
        ips = []
        for line in out.split('\n'):
            line_part = line.strip().split()
            if line == '' or line_part[0].isdigit() is False or len(line_part) == 1:
                continue
            else:
                for i in line_part[1:]:
                    try:
                        ip = i.split("/")[0]
                        if ip and IPy.IP(ip).version() == version:
                            ips.append(ip)
                            break
                    except:
                        continue
        return ips


class RouterOSAPI(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        if not kwargs or 'hostname' not in kwargs or 'username' not in kwargs or 'password' not in kwargs:
            return []
        ips = []
        path = "/ipv6/address" if version == 6 else "/ip/address"
        api = connect(username=kwargs['username'], password=kwargs['password'], host=kwargs['hostname'],
                      port=kwargs.get('port', 8728))
        ki = Key('interface')
        ka = Key('address')
        query = api.path(path).select(ki, ka)
        if interface:
            query = query.where(ki == interface)
        for i in query:
            ip = i['address'].split('/')[0]
            if ip and IPy.IP(ip).version() == version:
                ips.append(ip)
        return ips


class RouterOSREST(MethodBaseType):
    @staticmethod
    def getip(version: int = 4, interface: str = "", **kwargs) -> list:
        if not kwargs or 'hostname' not in kwargs or 'username' not in kwargs or 'password' not in kwargs:
            return []
        base = f"https://{kwargs['hostname']}:{kwargs.get("port", 443)}/rest"
        API = base + ("/ipv6/address" if version == 6 else "/ip/address")
        AUTH = HTTPBasicAuth(kwargs['username'], kwargs['password'])
        params = {}
        if interface:
            params = {"interface": interface}
        try:
            data = requests.get(API, auth=AUTH, params=params, timeout=3, verify=False).json()
            ips = []
            for raw in data:
                ip = raw['address'].split("/")[0]
                if ip and IPy.IP(ip).version() == version:
                    ips.append(ip)
            return ips
        except:
            return []
