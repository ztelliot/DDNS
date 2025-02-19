import logging
import requests
from requests.adapters import HTTPAdapter


class Gandi:
    def __init__(self, token: str):
        self.headers = {'X-Api-Key': token, 'Content-Type': 'application/json'}
        self.requests = requests.Session()
        self.requests.mount('http://', HTTPAdapter(max_retries=3))
        self.requests.mount('https://', HTTPAdapter(max_retries=3))

    def __req__(self, domain: str, record: str, type: str = None, method: str = "GET",
                **kwargs) -> tuple[bool, dict | None]:
        url = f'https://dns.api.gandi.net/api/v5/domains/{domain}/records/{record}' + ('/' + type if type else '')
        try:
            ret = self.requests.request(method=method, url=url, json=kwargs, headers=self.headers, timeout=3)
            ret.raise_for_status()
            return True, ret.json()
        except Exception as e:
            logging.error(f"Request error: {e}")
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
        if '默认' in ip_list:
            for type in ip_list['默认']:
                records = self.filter(sub_info, type)
                logging.debug(f"{type} filter records: {records}")
                ttl = ip_list['默认'][type]['ttl']
                ips = ip_list['默认'][type]['ip']
                if records:
                    if sorted(records) == sorted(ips):
                        logging.info(f'{sub}.{domain} {type} no need to update')
                        continue
                    elif ips:
                        status, result = self.__req__(domain, sub, type, 'PUT', rrset_ttl=ttl, rrset_values=ips)
                    else:
                        status, result = self.__req__(domain, sub, type, 'DELETE')
                else:
                    status, result = self.__req__(domain, sub, type, 'POST', rrset_ttl=ttl, rrset_values=ips)
                if status:
                    logging.info(f"update {sub}.{domain} {type} success")
                else:
                    logging.error(f"update {sub}.{domain} {type} failed, {result}")
