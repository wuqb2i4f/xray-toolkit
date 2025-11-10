from typing import Dict, Callable, Tuple

# Map config normalize strings to handlers: each returns (transformed_uri: str, target_proto: str)
normalizers: Dict[str, Callable[[str, str], Tuple[str, str]]] = {
    "map_to_hysteria2": lambda u, p: (u.replace(p, "hysteria2://", 1), "hysteria2"),
}
