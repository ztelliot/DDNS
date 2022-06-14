#!/usr/bin/python3
import yaml
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
        domain_ttl = i['ttl'] if 'ttl' in i else 600
        domain_clean = i['clean'] if 'clean' in i else False
        real_provider = provider_dict[provider]['provider'] if 'provider' in provider_dict[provider] else provider
        pv = providers[real_provider](provider_dict[provider]['config'])
        for j in i['sub']:
            sub = j['name']
            sub_ttl = j['ttl'] if 'ttl' in j else domain_ttl
            sub_clean = j['clean'] if 'clean' in j else domain_clean
            if not j['records']:
                j['records'] = [{}]
            logging.warning(f"开始处理 {sub}.{domain}")
            ip_list = {}
            for record in j['records']:
                type = record["type"] if "type" in record else "A"
                line = record["line"] if "line" in record else "默认"
                ttl = record["ttl"] if "ttl" in record else sub_ttl
                clean = record["clean"] if "clean" in record else sub_clean
                method = record["method"] if "method" in record else "requests"
                method_config = None
                if method in method_dict:
                    if 'config' in method_dict[method]:
                        method_config = method_dict[method]['config']
                    method = method_dict[method]['method'] if 'method' in method_dict[method] else method
                interface = record["interface"] if "interface" in record else ''
                start = record["start"] if "start" in record else ''
                ips = methods[method].getip(type, interface, start, config=method_config)
                logging.warning(f"{method} 方式获取到以下 IP : {ips}")
                if not ips and not clean:
                    continue
                if line not in ip_list:
                    ip_list[line] = {}
                if type not in ip_list[line]:
                    ip_list[line][type] = {'ttl': ttl, 'ip': []}
                ip_list[line][type]['ip'].extend(ips)
            logging.warning(f"共获取到以下 IP : {ip_list}")
            pv.update(domain, sub, ip_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="DDNS", description="Yet Another DDNS Script")
    parser.add_argument("--config", type=str, help="Specify config file path", default="config.yaml")
    arg = parser.parse_args()
    main(arg.config)
