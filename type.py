from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Literal, Tuple
from mashumaro.mixins.json import DataClassJSONMixin
import IPy

Methods = Literal["command", "curl", "interface", "requests", "routeros", "routeros-ssh", "routeros-rest"]
Providers = Literal["dnspod", "gandi"]
CustomAPI = Union[List[Union[str, Dict[str, str]]], str]
Records = Literal["A", "AAAA", "both"]


@dataclass
class IPInfo:
    interface: Optional[str] = None
    version: Optional[int] = None


@dataclass
class Provider:
    name: str
    config: Dict[str, str]
    provider: Optional[Providers] = None

    @property
    def real_provider(self):
        return self.provider if self.provider else self.name


@dataclass
class Method:
    name: str
    config: Dict[str, int | bool | str] = None
    method: Optional[Methods] = None

    @property
    def real_method(self):
        return self.method if self.method else self.name


@dataclass
class AddressBase:
    method: Optional[str] = None
    interface: Optional[str] = None
    regex: Optional[str] = None
    offset: Optional[Union[int, str]] = 0
    value: Optional[str] = None
    backup: Optional[bool] = False


@dataclass
class Address(AddressBase):
    name: Optional[str] = None
    version: Optional[int] = None

    @property
    def offset_int(self):
        if self.offset and isinstance(self.offset, str):
            return IPy.IP(self.offset).int()
        return self.offset


@dataclass
class RecordAddress(AddressBase):
    address: Optional[str] = None

    @property
    def real_method(self):
        return (self.method if self.method else "requests") if not self.address else None

    @property
    def suffix(self):
        return f"{self.real_method}_{self.interface}_{self.offset}_{self.regex}_{self.value}"

    def to_address(self, prefix: Optional[str] = None, version: Optional[int] = None) -> Address:
        return Address(name=f"{prefix}_{self.suffix}" if not self.address else self.address, version=version,
                       method=self.real_method, interface=self.interface, regex=self.regex, offset=self.offset,
                       value=self.value, backup=self.backup)


@dataclass
class Record:
    type: Optional[Records] = "both"
    line: Optional[str] = "默认"
    ttl: Optional[int] = None
    clean: Optional[bool] = None
    addresses: Optional[List[RecordAddress]] = None

    @property
    def suffix(self):
        return f"{self.type}_{self.line}"

    def extract_addresses(self, prefix: str) -> Tuple[List[str], List[Address]]:
        _version = None if self.type == "both" else (4 if self.type == "A" else 6)
        _address_prefix = f"{prefix}_{self.suffix}"
        reuse_addresses = []
        new_addresses = []
        if self.addresses:
            for a in self.addresses:
                if a.address:
                    reuse_addresses.append(a.address)
                elif not a.value:
                    new_addresses.append(a.to_address(_address_prefix, _version))
        else:
            new_addresses.append(Address(name=_address_prefix, version=_version))
        return reuse_addresses, new_addresses


@dataclass
class SubDomain:
    name: str
    records: List[Record]
    ttl: Optional[int] = None
    clean: Optional[bool] = None

    def extract_addresses(self, prefix: str) -> Tuple[List[str], List[Address]]:
        reuse_addresses = []
        new_addresses = []
        for r in self.records:
            _r, _n = r.extract_addresses(f"{prefix}_{self.name}")
            reuse_addresses.extend(_r)
            new_addresses.extend(_n)
        return reuse_addresses, new_addresses


@dataclass
class Domain:
    domain: str
    provider: str
    sub: List[SubDomain]
    ttl: Optional[int] = 600
    clean: Optional[bool] = False

    @property
    def prefix(self):
        return f"{self.provider}_{self.domain}"

    def extract_addresses(self) -> Tuple[List[str], List[Address]]:
        reuse_addresses = []
        new_addresses = []
        for s in self.sub:
            _r, _n = s.extract_addresses(self.prefix)
            reuse_addresses.extend(_r)
            new_addresses.extend(_n)
        return reuse_addresses, new_addresses


@dataclass
class Config(DataClassJSONMixin):
    providers: List[Provider]
    domains: List[Domain]
    methods: Optional[List[Method]] = None
    addresses: Optional[List[Address]] = None
    debug: Optional[bool] = False
