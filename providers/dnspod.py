import logging
import requests
from requests.adapters import HTTPAdapter
from copy import deepcopy


class DNSPod:
    def __init__(self, id: str, token: str, user: str = None):
        self.api = "https://dnsapi.cn/"
        self.__headers__ = {"User-Agent": "BIO DDNS/11.4.5.14 (ztell@foxmail.com)"}
        self.__data__ = {"login_token": f"{id},{token}", "format": "json", "lang": "cn", "error_on_empty": "no"}
        if user:
            self.__data__["user_id"] = user
        self.requests = requests.Session()
        self.requests.mount('http://', HTTPAdapter(max_retries=3))
        self.requests.mount('https://', HTTPAdapter(max_retries=3))

    def __post__(self, path, **kwargs) -> tuple[bool, dict]:
        data = deepcopy(self.__data__)
        code = False
        result = {}
        for k in kwargs:
            if kwargs[k] is not None:
                data[k] = kwargs[k]
        try:
            result = self.requests.post(self.api + path, data=data, headers=self.__headers__, timeout=5).json()
            status = result.get("status", {})
            if status.get("code") == "1":
                logging.debug(f"success: {status['message']}")
                code = True
            else:
                logging.warning(f"failed: {status['message']}")
            logging.debug(result)
        except Exception as e:
            logging.error(f"Request error: {e}")
        finally:
            return code, result

    def record_create(self, domain: str, value: str, **kwargs) -> str:
        kwargs.setdefault("sub_domain", "")
        kwargs.setdefault("record_type", "A")
        kwargs.setdefault("record_line", "默认")
        kwargs.setdefault("mx", 0)
        kwargs.setdefault("ttl", 600)
        status, data = self.__post__("Record.Create", domain=domain, value=value, **kwargs)
        return None if status else data.get("record", {}).get("id")

    def record_list(self, domain: str, **kwargs) -> list[dict]:
        kwargs.setdefault("sub_domain", "")
        records = []
        offset = 0
        while True:
            status, data = self.__post__("Record.List", length=100, offset=offset, domain=domain, **kwargs)
            if status:
                records.extend(data["records"])
                if int(data["info"]["record_total"]) > offset + int(data["info"]["records_num"]):
                    offset += data["info"]["records_num"]
                else:
                    break
            else:
                break
        return records

    @staticmethod
    def record_filter(records: list, record_type: str = "A", record_line: str = "默认") -> dict[str, str]:
        record_filtered = {}
        if not records:
            return {}
        for record in records:
            if record["enabled"] == "1" and record["type"] == record_type and record["line"] == record_line:
                record_filtered[record["value"]] = record["id"]
        return deepcopy(record_filtered)

    def record_modify(self, domain: str, record_id: str, value: str, **kwargs) -> bool:
        kwargs.setdefault("sub_domain", "")
        kwargs.setdefault("record_type", "A")
        kwargs.setdefault("record_line", "默认")
        kwargs.setdefault("mx", 0)
        kwargs.setdefault("ttl", 600)
        status, _ = self.__post__("Record.Modify", domain=domain, record_id=record_id, value=value, **kwargs)
        return status

    def record_remove(self, domain: str, record_id: str) -> bool:
        status, _ = self.__post__("Record.Remove", domain=domain, record_id=record_id)
        return status

    def record_ddns(self, domain: str, record_id: str, **kwargs) -> bool:
        kwargs.setdefault("value", None)
        kwargs.setdefault("sub_domain", "")
        kwargs.setdefault("record_line", "默认")
        status, _ = self.__post__("Record.Ddns", domain=domain, record_id=record_id, **kwargs)
        return status

    def update(self, domain: str, sub: str, ip_list: dict):
        sub_info = self.record_list(domain=domain, sub_domain=sub)
        for line in ip_list:
            for type in ip_list[line]:
                records = self.record_filter(sub_info, type, line)
                records_list = list(records.keys())
                logging.debug(f"{line} {type} filter records: {records}")
                ttl = ip_list[line][type]['ttl']
                ips = deepcopy(ip_list[line][type]['ip'])
                for ip in ip_list[line][type]['ip']:
                    if ip in records:
                        logging.debug(f"{ip} exists in records")
                        del records[ip]
                        ips.remove(ip)
                        records_list.remove(ip)
                if len(records_list) < len(ips):
                    logging.debug("records less than ips, create new records...")
                    logging.debug(f"before: {records_list}, after: {ips}")
                    new = deepcopy(ips[0: len(ips) - len(records_list)])
                    for ip in new:
                        if self.record_create(domain, ip, sub_domain=sub, record_type=type, record_line=line, ttl=ttl):
                            logging.debug(f"create {ip} success")
                        else:
                            logging.error(f"create {ip} failed")
                        ips.remove(ip)
                elif len(records_list) > len(ips):
                    logging.debug("records more than ips, remove extra records...")
                    old = deepcopy(records[0: len(records_list) - len(ips)])
                    for ip in old:
                        if self.record_remove(domain, records[ip]):
                            logging.debug(f"remove {ip} success")
                        else:
                            logging.error(f"remove {ip} failed")
                        del records[ip]
                        records_list.remove(ip)
                for ip, old_ip in zip(ips, records_list):
                    if self.record_modify(domain, records[old_ip], ip, sub_domain=sub, record_type=type,
                                          record_line=line, ttl=ttl):
                        logging.debug(f"modify {old_ip} to {ip} success")
                    else:
                        logging.error(f"modify {old_ip} failed, try to use DDNS...")
                        if self.record_ddns(domain, records[old_ip], value=ip, sub_domain=sub, record_line=line):
                            logging.debug(f"DDNS {old_ip} to {ip} success")
                        else:
                            logging.error(f"DDNS {old_ip} failed")
