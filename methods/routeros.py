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
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        if not config:
            return []
        if type == "AAAA":
            command = "/ipv6 "
        else:
            command = "/ip "
        command += "address print "
        if interface:
            command += "where interface=" + interface
        out = Command.run({'cmd': command, 'ssh': config})
        ips = []
        for line in out.split('\n'):
            line_part = line.strip().split()
            if line == '' or line_part[0].isdigit() is False or len(line_part) == 1:
                continue
            else:
                for i in line_part[1:]:
                    try:
                        ip = i.split("/")[0]
                        IPy.IP(ip)
                        if ip.startswith(start):
                            ips.append(ip)
                            break
                    except:
                        continue
        return ips


class RouterOSAPI(MethodBaseType):
    @staticmethod
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        if not config:
            return []
        if 'hostname' not in config or 'username' not in config or 'password' not in config:
            return []
        ips = []
        if type == "AAAA":
            path = "/ipv6/address"
        else:
            path = "/ip/address"
        api = connect(username=config['username'], password=config['password'], host=config['hostname'],
                      port=config['port'] if 'port' in config else 8728)
        ki = Key('interface')
        ka = Key('address')
        query = api.path(path).select(ki, ka)
        if interface:
            query = query.where(ki == interface)
        for i in query:
            ip = i['address'].split('/')[0]
            if ip.startswith(start):
                ips.append(ip)
        return ips


class RouterOSREST(MethodBaseType):
    @staticmethod
    def getip(type: str = "A", interface: str = "", start: str = "", config: dict = None) -> list:
        if not config:
            return []
        if 'hostname' not in config or 'username' not in config or 'password' not in config:
            return []
        base = f"https://{config['hostname']}:{config['port'] if 'port' in config else 443}/rest"
        if type == "AAAA":
            API = base + "/ipv6/address"
        else:
            API = base + "/ip/address"
        AUTH = HTTPBasicAuth(config['username'], config['password'])
        params = {}
        if interface:
            params = {"interface": interface}
        try:
            data = requests.get(API, auth=AUTH, params=params, timeout=3, verify=False).json()
            ips = []
            for raw in data:
                ip = raw['address'].split("/")[0]
                if ip.startswith(start):
                    ips.append(ip)
            return ips
        except:
            return []
