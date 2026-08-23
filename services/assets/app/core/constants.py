"""Shared enums and constants for Layer 3 - Asset Intelligence."""
from enum import Enum


class EntityType(str, Enum):
    IP_ADDRESS = "ip_address"
    HOSTNAME = "hostname"
    MAC_ADDRESS = "mac_address"
    USERNAME = "username"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    PROCESS = "process"
    CVE = "cve"
    PORT = "port"
    EMAIL = "email"
    ASSET = "asset"


class EdgeType(str, Enum):
    IP_TO_HOSTNAME = "ip_to_hostname"
    IP_TO_MAC = "ip_to_mac"
    USER_TO_HOST = "user_to_host"
    USER_TO_IP = "user_to_ip"
    HOST_TO_PROCESS = "host_to_process"
    PROCESS_TO_HASH = "process_to_hash"
    IP_TO_DOMAIN = "ip_to_domain"
    DOMAIN_TO_URL = "domain_to_url"
    HOST_TO_CVE = "host_to_cve"
    IP_TO_PORT = "ip_to_port"
    IOC_TO_ENTITY = "ioc_to_entity"
    COMMUNICATES_WITH = "communicates_with"
    AUTHENTICATED_AS = "authenticated_as"
    RESOLVES_TO = "resolves_to"
    ASSOCIATED_WITH = "associated_with"
    ASSET_TO_CVE = "asset_to_cve"


class LogSourceType(str, Enum):
    FIREWALL = "firewall"
    IDS = "ids"
    IPS = "ips"
    SYSMON = "sysmon"
    AUTH = "auth"
    DNS = "dns"
    UNKNOWN = "unknown"


class IOCType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH_MD5 = "hash_md5"
    HASH_SHA1 = "hash_sha1"
    HASH_SHA256 = "hash_sha256"
    EMAIL = "email"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
