import logging
import requests
from requests.adapters import HTTPAdapter


class DNSPod:
    def __init__(self, config: dict):
        self.api = "https://dnsapi.cn/"
        self.__headers__ = {"User-Agent": config['ua']}
        self.__data__ = {"login_token": f"{config['id']},{config['token']}", "format": "json", "lang": "cn",
                         "error_on_empty": "no"}
        if 'user' in config and config['user']:
            self.__data__["user_id"] = config['user']
        self.requests = requests.Session()
        self.requests.mount('http://', HTTPAdapter(max_retries=3))
        self.requests.mount('https://', HTTPAdapter(max_retries=3))

    def __post__(self, path, **kwargs) -> tuple:
        data = self.__data__
        code = False
        result = None
        for key in kwargs:
            if kwargs[key] is not None:
                data[key] = kwargs[key]
        try:
            result = self.requests.post(self.api + path, data=data, headers=self.__headers__, timeout=3).json()
            if "status" in result:
                status = result["status"]
                if status["code"] == "1":
                    logging.debug(f"操作成功: {status['message']}")
                    code = True
                else:
                    logging.warning(f"操作失败: {status['message']}")
            logging.debug(result)
        except:
            pass
        finally:
            return code, result

    def RecordCreate(self, domain: str, value: str, sub: str = "", type: str = "A", line: str = "默认", mx: int = 0,
                     ttl: int = 600) -> str:
        path = "Record.Create"
        record_id = None
        status, data = self.__post__(path, domain=domain, sub_domain=sub, record_type=type, record_line=line,
                                     value=value, mx=mx, ttl=ttl)
        if status:
            record_id = data["record"]["id"]
        return record_id

    def RecordList(self, domain: str, sub: str = "") -> list:
        path = "Record.List"
        records = []
        offset = 0
        while True:
            status, data = self.__post__(path, domain=domain, sub_domain=sub, length=100, offset=offset)
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
    def RecordFilter(records: list, record_type: str = "A", record_line: str = "默认") -> dict:
        record_filtered = {}
        if not records:
            return {}
        for record in records:
            if record["enabled"] == "1" and record["type"] == record_type and record["line"] == record_line:
                record_filtered[record["value"]] = record["id"]
        return record_filtered

    def RecordModify(self, domain: str, record: str, value: str, sub: str = "", type: str = "A", line: str = "默认",
                     mx: int = 0, ttl: int = 600) -> bool:
        path = "Record.Modify"
        status, _ = self.__post__(path, domain=domain, record_id=record, sub_domain=sub, record_type=type,
                                  record_line=line, value=value, mx=mx, ttl=ttl)
        return status

    def RecordRemove(self, domain: str, record: str) -> bool:
        path = "Record.Remove"
        status, _ = self.__post__(path, domain=domain, record_id=record)
        return status

    def RecordDdns(self, domain: str, record: str, value: str = None, sub: str = "", line: str = "默认") -> bool:
        path = "Record.Ddns"
        status, _ = self.__post__(path, domain=domain, record_id=record, sub_domain=sub, record_line=line, value=value)
        return status

    def update(self, domain: str, sub: str, ip_list: dict):
        sub_info = self.RecordList(domain=domain, sub=sub)
        for line in ip_list:
            for type in ip_list[line]:
                records = self.RecordFilter(sub_info, type, line)
                records_list = [i for i in records]
                logging.debug(f"根据 {line} {type} 筛选出下列记录: {records}")
                ttl = ip_list[line][type]['ttl']
                ips = [i for i in ip_list[line][type]['ip']]
                for ip in [i for i in ips]:
                    if ip in records:
                        logging.warning(f"{ip} 已在记录列表中, 跳过...")
                        del records[ip]
                        ips.remove(ip)
                        records_list.remove(ip)
                if len(records_list) < len(ips):
                    logging.warning("记录条数少于 IP 数, 新建记录...")
                    logging.debug(f"原记录为: {records_list} , 现 IP 为 {ips}")
                    for ip in ips[0: len(ips) - len(records_list)]:
                        if self.RecordCreate(domain, ip, sub, type, line, ttl=ttl):
                            logging.warning(f"新建 {ip} 成功")
                        else:
                            logging.warning(f"新建 {ip} 失败")
                        ips.remove(ip)
                elif len(records_list) > len(ips):
                    logging.warning("记录条数多于 IP 数, 删除多余记录...")
                    t = [i for i in records][0: len(records_list) - len(ips)]
                    for old_ip in t:
                        if self.RecordRemove(domain, records[old_ip]):
                            logging.warning(f"删除 {old_ip} 成功")
                        else:
                            logging.warning(f"删除 {old_ip} 失败")
                        del records[old_ip]
                        records_list.remove(old_ip)
                for ip, old_ip in zip(ips, records_list):
                    if self.RecordModify(domain, records[old_ip], ip, sub, type, line, ttl=ttl):
                        logging.warning(f"更新记录成功, {old_ip} => {ip}")
                    else:
                        logging.warning(f"更新 {old_ip} 失败, 尝试使用 DDNS 方式更新...")
                        if self.RecordDdns(domain, records[old_ip], ip, sub, line):
                            logging.warning(f"使用 DDNS 方式更新记录成功, {old_ip} => {ip}")
                        else:
                            logging.warning(f"使用 DDNS 方式更新 {old_ip} 失败")
