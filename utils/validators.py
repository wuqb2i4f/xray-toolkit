import re
import uuid
from typing import Dict, Callable


def validate_ipv4(addr: str) -> bool:
    return bool(re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", addr)) and all(
        0 <= int(o) <= 255 for o in addr.split(".")
    )


def validate_ipv6(addr: str) -> bool:
    return bool(re.match(r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$", addr))


def validate_domain(addr: str) -> bool:
    return bool(
        re.match(
            r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
            addr,
        )
    )


def validate_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False


# Map config validator strings to functions
validators_map: Dict[str, Callable[[str], bool]] = {
    "ipv4": validate_ipv4,
    "ipv6": validate_ipv6,
    "domain": validate_domain,
    "uuid": validate_uuid,
}
