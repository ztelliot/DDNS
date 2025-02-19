import jsonpath
import json
from typing import Iterable

_api = [
    {
        "url": "https://pubstatic.b0.upaiyun.com/?_upnode",
        "key": "$.remote_addr"
    }, {
        "url": "http://myip6.ipip.net/ip",
        "key": "$.ip"
    },
    "https://cdid.c-ctrip.com/model-poc2/h",
    "https://speed.neu.edu.cn/getIP.php",
    "http://api.ip.sb/ip",
    {
        "url": "https://wsus.sjtu.edu.cn/speedtest/backend/getIP.php",
        "key": "$.processedString"
    }, {
        "url": "https://api.bilibili.com/x/web-interface/zone",
        "key": "$.data.addr"
    }, {
        "url": "https://api.live.bilibili.com/ip_service/v1/ip_service/get_ip_addr",
        "key": "$.data.addr"
    }
]


class API:
    url: str
    key: str = ""

    def __init__(self, url: str, key: str = ""):
        self.url = url
        if not url:
            raise ValueError("API url is required")
        self.key = key

    def parse(self, data: str) -> str:
        if self.key:
            try:
                ip = jsonpath.findall(self.key, json.loads(data))
                return ip[0] if ip else ''
            except:
                return ''
        return data


def get_api(custom: list[str | dict[str, str]] | str = None) -> Iterable[API]:
    api_list = (custom if isinstance(custom, list) else [custom]) if custom else _api
    for api in api_list:
        if isinstance(api, dict):
            yield API(api.get("url"), api.get("key", ''))
        else:
            yield API(api)
