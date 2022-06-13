from methods.command import Command
from methods.curl import Curl
from methods.interface import Interface
from methods.requests import Requests
from methods.routeros import RouterOS, RouterOSREST

methods = {
    "command": Command,
    "curl": Curl,
    "interface": Interface,
    "requests": Requests,
    "routeros": RouterOS,
    "routeros-rest": RouterOSREST
}
