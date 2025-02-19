from methods.base import Method
from methods.command import Command
import urllib3
import requests
from requests.auth import HTTPBasicAuth
from librouteros import connect
from librouteros.query import Key

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RouterOSSSH(Method):
    @staticmethod
    def run(version: int = None, interface: str = None, **kwargs) -> dict[str, dict[str, str]]:
        if not kwargs:
            return {}
        command = "/ip " if version == 4 else "/ipv6 "
        command += "address print value-list without-paging "
        if interface:
            command += "where interface=" + interface
        out = Command.exec(command=command, ssh=kwargs)
        ips = {}
        _address, _interface = [], []
        for line in out.split('\n'):
            _line = line.strip()
            if _line.startswith('address:'):
                _address = _line.split()[1:]
            elif _line.startswith('interface:'):
                _interface = _line.split()[1:]
            if _address and _interface:
                break
        if _address and _interface and len(_address) == len(_interface):
            for _a, _i in zip(_address, _interface):
                if _a:
                    ips[_a] = {"interface": _i} if _i else {}
        return ips


class RouterOSAPI(Method):
    @staticmethod
    def run(hostname: str, username: str, password: str, port: int = 8728, version: int = None,
            interface: str = None) -> dict[str, dict[str, str]]:
        path = "/ip/address" if version == 4 else "/ipv6/address"
        api = connect(username=username, password=password, host=hostname, port=port)
        ki = Key('interface')
        ka = Key('address')
        query = api.path(path).select(ki, ka)
        if interface:
            query = query.where(ki == interface)
        ips = {}
        for i in query:
            _ip = i['address'].split('/')[0]
            if _ip:
                ips[_ip] = {"interface": i['interface']} if i['interface'] else {}
        return ips


class RouterOSREST(Method):
    @staticmethod
    def run(hostname: str, username: str, password: str, port: int = 443, version: int = None,
            interface: str = None) -> dict[str, dict[str, str]]:
        api = f"https://{hostname}:{port}/rest/ip{'' if version == 4 else 'v6'}/address"
        auth = HTTPBasicAuth(username, password)
        params = {}
        if interface:
            params = {"interface": interface}
        data = requests.get(api, auth=auth, params=params, timeout=5, verify=False).json()
        ips = {}
        for raw in data:
            _ip = raw['address'].split("/")[0]
            if _ip:
                ips[_ip] = {"interface": raw['interface']} if raw['interface'] else {}
        return ips
