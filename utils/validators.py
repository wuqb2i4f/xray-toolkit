import re
from typing import Dict, Callable

# Map config validator strings to functions (extend by adding here)
validators_map: Dict[str, Callable[[str], bool]] = {
    "ipv4": lambda addr: bool(re.match(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", addr))
    and all(0 <= int(o) <= 255 for o in addr.split(".")),
    "ipv6": lambda addr: bool(
        re.match(r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$", addr)
    ),
    "domain": lambda addr: bool(
        re.match(
            r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
            addr,
        )
    ),
}
