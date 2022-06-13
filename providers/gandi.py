import logging
import requests
from requests.adapters import HTTPAdapter


class Gandi:
    def __init__(self, config: dict):
        self.headers = {'X-Api-Key': config['token'], 'Content-Type': 'application/json'}
        self.requests = requests.Session()
        self.requests.mount('http://', HTTPAdapter(max_retries=3))
        self.requests.mount('https://', HTTPAdapter(max_retries=3))

    def __req__(self, domain: str, record: str, type: str = None, data: dict = None, method: str = "GET") -> tuple:
        url = f'https://dns.api.gandi.net/api/v5/domains/{domain}/records/{record}' + ('/' + type if type else '')
        try:
            ret = self.requests.request(method=method, url=url, json=data, headers=self.headers, timeout=3)
            ret.raise_for_status()
            return True, ret.json()
        except:
            pass
        finally:
            return False, None

    @staticmethod
    def filter(records: list, type: str) -> list:
        record_filtered = []
        for record in records:
            if record["rrset_type"] == type:
                record_filtered.extend(record['rrset_values'])
        return record_filtered

    def update(self, domain: str, sub: str, ip_list: dict):
        status, sub_info = self.__req__(domain, sub)
        if not status or not sub_info:
            sub_info = []
        for type in ip_list:
            if '默认' in ip_list[type]:
                records = self.filter(sub_info, type)
                logging.debug(f"根据 {type} 筛选出下列记录: {records}")
                ips = [i for i in ip_list[type]['默认']]
                if records:
                    if sorted(records) == sorted(ips):
                        logging.warning(f'{sub}.{domain} {type} 无需更新')
                    else:
                        status, result = self.__req__(domain, sub, type, {"rrset_ttl": 300, "rrset_values": ips}, 'PUT')
                        if status:
                            logging.warning(f"更新 {sub}.{domain} {type} 成功")
                        else:
                            logging.warning(f"更新 {sub}.{domain} {type} 失败，{result}")
                else:
                    status, result = self.__req__(domain, sub, type, {"rrset_ttl": 300, "rrset_values": ips}, 'POST')
                    if status:
                        logging.warning(f"新建 {sub}.{domain} {type} 成功")
                    else:
                        logging.warning(f"新建 {sub}.{domain} {type} 失败，{result}")
