from methods.base import Method
from methods.command import Command
from methods.api import get_api


class Curl(Method):
    @staticmethod
    def run(version: int = None, interface: str = None, url: list[str | dict[str, str]] | str = None,
            **kwargs) -> dict[str, dict[str, str]]:
        command = "curl -m 10 "
        if version:
            command += f"-{version} "
        if interface:
            command += f"--interface {interface} "
        for api in get_api(url):
            out = Command.exec(command=command + api.url, **kwargs)
            ip = api.parse(out)
            if ip:
                return {ip: {"interface": interface} if interface else {}}
        return {}
