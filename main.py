#!/usr/bin/python3
import IPy
import yaml
import re
import logging
import argparse
from methods import methods
from providers import providers

logging.basicConfig(level=logging.WARNING, format="[%(asctime)s] %(message)s")


def main(config: str = "config.yaml"):
    config = yaml.safe_load(open(config).read())
    logging.warning("开始更新 DNS 记录")
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
            logging.warning(f"开始处理 {sub}.{domain}")
            ip_list = {}
            for record in j['records']:
                type = record.get("type", "A")
                version = 6 if type == 'AAAA' else 4
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
                    ips = methods[method].getip(version, interface, config=method_config)
                    ips_regex = [ip for ip in ips if re.match(regex, ip)]
                    logging.warning(f"{method} 方式获取到以下 IP : {ips_regex}")
                else:
                    ips_regex = [record["value"]]
                offset = record.get("offset", 0)
                if offset:
                    if isinstance(offset, str):
                        try:
                            offset = IPy.IP(offset).int()
                        except:
                            pass
                    ips_offset = []
                    for ip in ips_regex:
                        try:
                            _ip = IPy.IP(ip)
                            ips_offset.append(IPy.intToIp(_ip.int() + offset, _ip.version()))
                        except:
                            ips_offset.append(ip)
                    ips_regex = ips_offset
                if not ips_regex and not clean:
                    continue
                if line not in ip_list:
                    ip_list[line] = {}
                if type not in ip_list[line]:
                    ip_list[line][type] = {'ttl': ttl, 'ip': []}
                ip_list[line][type]['ip'].extend(ips_regex)
            logging.warning(f"共获取到以下 IP : {ip_list}")
            pv.update(domain, sub, ip_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="DDNS", description="Yet Another DDNS Script")
    parser.add_argument("--config", type=str, help="Specify config file path", default="config.yaml")
    arg = parser.parse_args()
    main(arg.config)
