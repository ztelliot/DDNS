from methods.base import Method
from methods.interface import Interface
from methods.api import get_api
import requests
import socket
import urllib3.util.connection as urllib3
import logging


class Requests(Method):
    @staticmethod
    def run(version: int = None, interface: str = None, url: list[str | dict[str, str]] | str = None, **kwargs) -> dict[str, dict[str, str]]:
        default_gai = urllib3.allowed_gai_family
        if version:
            urllib3.allowed_gai_family = (lambda : socket.AF_INET) if version == 4 else (lambda : socket.AF_INET6)

        default_connection = urllib3.create_connection
        if interface:
            _interface_ips = Interface.run(version, interface)
            if _interface_ips:
                _source_address = (list(_interface_ips.keys())[0], 0)
                urllib3.create_connection = lambda address, timeout, source_address=None, socket_options=None: default_connection(address, timeout, _source_address, socket_options)
            else:
                urllib3.allowed_gai_family = default_gai
                return {}

        res = {}
        for api in get_api(url):
            try:
                ret = requests.get(api.url, timeout=5)
                ip = api.parse(ret.text)
                if ip:
                    res[ip] = {"interface": interface} if interface else {}
                    break
            except Exception as e:
                logging.error(f"Failed to get ip from {api.url}: {e}")
                continue

        urllib3.allowed_gai_family = default_gai
        urllib3.create_connection = default_connection

        return res
