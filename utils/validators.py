import re
import uuid


def validate_ipv4(addr):
    return bool(re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", addr)) and all(
        0 <= int(o) <= 255 for o in addr.split(".")
    )


def validate_ipv6(addr):
    return bool(re.match(r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$", addr))


def validate_domain(addr):
    return bool(
        re.match(
            r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
            addr,
        )
    )


def validate_host(host):
    return any(
        re.match(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$", label) and len(label) <= 63
        for label in str(host).split(".")
        if label and not label.isdigit() and "--" not in label
    )


def validate_port(value: int) -> bool:
    return isinstance(value, int) and 1 <= value <= 65535


def validate_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False


validators_map = {
    "ipv4": validate_ipv4,
    "ipv6": validate_ipv6,
    "domain": validate_domain,
    "port": validate_port,
    "uuid": validate_uuid,
    "host": validate_host,
}
