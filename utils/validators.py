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


def validate_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False


def validate_path(path):
    if not path.startswith("/"):
        return False
    return bool(re.match(r"^/[^ ]*$", path))


validators_map = {
    "ipv4": validate_ipv4,
    "ipv6": validate_ipv6,
    "domain": validate_domain,
    "uuid": validate_uuid,
    "path": validate_path,
}
