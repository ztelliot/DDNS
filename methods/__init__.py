from methods.command import Command
from methods.curl import Curl
from methods.interface import Interface
from methods.requests import Requests
from methods.routeros import RouterOSSSH, RouterOSAPI, RouterOSREST

methods = {
    "command": Command,
    "curl": Curl,
    "interface": Interface,
    "requests": Requests,
    "routeros": RouterOSAPI,
    "routeros-ssh": RouterOSSSH,
    "routeros-rest": RouterOSREST
}
