#!/usr/bin/python3
import IPy
import yaml
import re
import logging
import argparse
from methods import methods
from providers import providers

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")


def main(config: str = "config.yaml"):
    config = yaml.safe_load(open(config).read())
    logging.info("开始更新 DNS 记录")
    provider_dict = {i['name']: i for i in config['providers']} if config['providers'] else {}
    method_dict = {i['name']: i for i in config['methods']} if config['methods'] else {}
    for i in config['domains']:
        domain = i['domain']
        provider = i['provider']
        domain_ttl = i.get("ttl", 600)
        domain_clean = i.get("clean", False)
        real_provider = provider_dict[provider].get("provider", provider)
        pv = providers[real_provider](provider_dict[provider]['config'])
        for j in i['sub']:
            sub = j['name']
            sub_ttl = j.get('ttl', domain_ttl)
            sub_clean = j.get('clean', domain_clean)
            if not j['records']:
                j['records'] = [{}]
            logging.info(f"开始处理 {sub}.{domain}")
            ip_list = {}
            for record in j['records']:
                type = record.get("type", "AAAA")
                version = 4 if type == 'A' else 6
                line = record.get("line", "默认")
                ttl = record.get("ttl", sub_ttl)
                clean = record.get("clean", sub_clean)
                if not record.get("value"):
                    method = record.get("method", "requests")
                    method_config = None
                    if method in method_dict:
                        if 'config' in method_dict[method]:
                            method_config = method_dict[method]['config']
                        method = method_dict[method].get('method', method)
                    interface = record.get("interface", '')
                    regex = record.get("regex", '')
                    offset = record.get("offset", 0)
                    if offset and isinstance(offset, str):
                        try:
                            offset = IPy.IP(offset).int()
                        except Exception as e:
                            logging.error(f"offset 参数解析失败: {e}")
                            raise e
                    try:
                        _ips = methods[method].getip(version, interface, config=method_config)
                    except Exception as e:
                        logging.error(f"获取 IP 失败: {e}")
                        continue
                    logging.debug(f"{method} 方式获取到以下 IP : {_ips}")
                    ips = []
                    for _ip in _ips:
                        if regex and not re.match(regex, _ip):
                            continue
                        try:
                            _ip_obj = IPy.IP(_ip)
                            if _ip_obj.version() != version:
                                continue
                            if offset:
                                ips.append(IPy.intToIp(_ip_obj.int() + offset, version))
                            else:
                                ips.append(_ip)
                        except Exception as e:
                            logging.error(f"IP 解析失败: {e}")
                            continue
                    logging.info(f"根据 {method} 获取到以下 IP : {ips}")
                else:
                    ips = [record["value"]]
                if not ips and not clean:
                    continue
                if line not in ip_list:
                    ip_list[line] = {}
                if type not in ip_list[line]:
                    ip_list[line][type] = {'ttl': ttl, 'ip': []}
                ip_list[line][type]['ip'].extend(ips)
            logging.info(f"共获取到以下 IP : {ip_list}")
            pv.update(domain, sub, ip_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="DDNS", description="Yet Another DDNS Script")
    parser.add_argument("--config", type=str, help="Specify config file path", default="config.yaml")
    arg = parser.parse_args()
    main(arg.config)
