#!/usr/bin/python3
import yaml
import logging
from methods import methods
from providers import providers


logging.basicConfig(level=logging.WARNING, format="[%(asctime)s] %(message)s")


def main():
    logging.warning("开始更新 DNS 记录")
    config = yaml.safe_load(open('config.yaml').read())
    provider_dict = {i['name']: i for i in config['providers']} if config['providers'] else {}
    method_dict = {i['name']: i for i in config['methods']} if config['methods'] else {}
    for i in config['domains']:
        domain = i['domain']
        provider = i['provider']
        real_provider = provider_dict[provider]['provider'] if 'provider' in provider_dict[provider] else provider
        pv = providers[real_provider](provider_dict[provider]['config'])
        for j in i['sub']:
            sub = j['name']
            if not j['records']:
                j['records'] = [{}]
            logging.warning(f"开始处理 {sub}.{domain}")
            ip_list = {"A": {}, "AAAA": {}}
            for record in j['records']:
                type = record["type"] if "type" in record else "A"
                line = record["line"] if "line" in record else "默认"
                ttl = record["ttl"] if "ttl" in record else 600
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
                if not ips:
                    continue
                if line not in ip_list[type]:
                    ip_list[type][line] = {}
                for ip in ips:
                    ip_list[type][line][ip] = ttl
            logging.warning(f"共获取到以下 IP : {ip_list}")
            pv.update(domain, sub, ip_list)


if __name__ == '__main__':
    main()
