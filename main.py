#!/usr/bin/python3
import IPy
import yaml
import re
import logging
import argparse
from methods import methods
from providers import providers
from type import Config, IPInfo, Address

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")


def address_filter(ips: dict[str, IPInfo], address: Address) -> dict[str, IPInfo]:
    results = {}
    for i in ips:
        if address.interface and (not ips[i] or ips[i].interface != address.interface):
            continue
        if address.regex and not re.match(address.regex, i):
            continue
        try:
            _ip_obj = None
            if not ips[i].version:
                _ip_obj = IPy.IP(i)
                ips[i].version = _ip_obj.version()
            if address.version and ips[i].version != address.version:
                continue
            if address.offset:
                if not _ip_obj:
                    _ip_obj = IPy.IP(i)
                _ip_offset = IPy.IP(_ip_obj.int() + address.offset_int, _ip_obj.version()).strCompressed()
                results[_ip_offset] = ips[i]
            else:
                results[i] = ips[i]
        except Exception as e:
            logging.error(f"failed parsing IP: {e}")
    return results


def main(config: str = "config.yaml"):
    logging.info("parse config file")
    config = Config.from_dict(yaml.safe_load(open(config, encoding="utf-8").read()))
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    _providers = {i.name: i for i in config.providers}
    _methods = {i.name: i for i in config.methods} if config.methods else {}

    logging.info("extract addresses")
    _addresses = {i.name: i for i in config.addresses if i.name} if config.addresses else {}
    _addresses_usage = {i.name: False for i in config.addresses if i.name} if config.addresses else {}
    for d in config.domains:
        if d.provider not in _providers:
            raise ValueError(f"provider {d.provider} not found")
        _reuse_addresses, _new_addresses = d.extract_addresses()
        for i in _reuse_addresses:
            _addresses_usage[i] = True
        for i in _new_addresses:
            _addresses[i.name] = i
            _addresses_usage[i.name] = True
    _addresses_keys = list(_addresses.keys())
    for _a in _addresses_keys:
        if not _addresses_usage.get(_a):
            logging.warning(f"address {_a} is not used")
            del _addresses[_a]
    logging.info("%d addresses extracted", len(_addresses))

    logging.info("fetch addresses")
    _addresses_result = {}
    for _a in _addresses:
        _address = _addresses[_a]
        if _address.method not in _methods:
            raise ValueError(f"method {_address.method} not found")
        _method = _methods[_address.method]
        try:
            _arr = methods[_method.real_method].getip(version=_address.version, interface=_address.interface,
                                                      **_method.config)
            _addresses_result[_a] = address_filter(_arr, _address)
        except Exception as e:
            logging.error(f"{_method.real_method} getip failed: {e}")
            continue
    logging.info("addresses fetched")

    logging.info("update dns")
    for d in config.domains:
        _provider = _providers[d.provider]
        _provider_obj = providers[_provider.real_provider](**_provider.config)
        for s in d.sub:
            sub_ttl = s.ttl if s.ttl else d.ttl
            sub_clean = s.clean if s.clean else d.clean

            logging.info(f"update {s.name}.{d.domain}")
            ip_list = {}
            for r in s.records:
                line = r.line if r.line else "默认"
                ttl = r.ttl if r.ttl else sub_ttl
                clean = r.clean if r.clean else sub_clean

                _record_addresses = []
                if not r.addresses:
                    _ak = f"{d.prefix}_{s.name}_{r.suffix}"
                    if _ak not in _addresses_result:
                        logging.warning(f"address {_ak} not found")
                        continue
                    _record_addresses.extend(_addresses_result[_ak].keys())
                    continue
                for _a in r.addresses:
                    if _record_addresses and _a.backup:
                        continue
                    if _a.value:
                        _record_addresses.append(_a.value)
                        continue
                    _aa = _a.to_address(f"{d.prefix}_{s.name}_{r.suffix}",
                                        None if r.type == "both" else (4 if r.type == "A" else 6))
                    if _aa.name not in _addresses_result:
                        logging.warning(f"address {_aa} not found")
                        continue
                    _record_addresses.extend(address_filter(_addresses_result[_aa.name], _aa).keys())
                logging.info(f"%d records of {r.suffix} filtered", len(_record_addresses))
                logging.debug(f"records: {_record_addresses}")
                if not _record_addresses and not clean:
                    logging.debug(f"skip {r.suffix}")
                    continue

                if line not in ip_list:
                    ip_list[line] = {}
                if r.type != "both":
                    if r.type not in ip_list[line]:
                        ip_list[line][r.type] = {'ttl': ttl, 'ip': []}
                    ip_list[line][r.type]['ip'].extend(_record_addresses)
                else:
                    if "A" not in ip_list[line]:
                        ip_list[line]["A"] = {'ttl': ttl, 'ip': []}
                    ip_list[line]["A"]['ip'].extend([i for i in _record_addresses if '.' in i])
                    if "AAAA" not in ip_list[line]:
                        ip_list[line]["AAAA"] = {'ttl': ttl, 'ip': []}
                    ip_list[line]["AAAA"]['ip'].extend([i for i in _record_addresses if ':' in i])
                logging.info(f"target record: {ip_list}")
            _provider_obj.update(d.domain, s.name, ip_list)
            logging.info(f"{s.name}.{d.domain} updated")
    logging.info("done")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="DDNS", description="Yet Another DDNS Script")
    parser.add_argument("--config", type=str, help="Specify config file path", default="config.yaml")
    arg = parser.parse_args()
    main(arg.config)
