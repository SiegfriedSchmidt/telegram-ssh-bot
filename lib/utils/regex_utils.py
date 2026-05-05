import re


def is_valid_mac_address(mac: str) -> bool:
    patterns = [
        r'^[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}$',
        r'^[0-9A-Fa-f]{12}$',
        r'^[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}$',
    ]
    return any(re.match(pattern, mac) for pattern in patterns)
