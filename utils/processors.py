from typing import Dict, Callable, Tuple


# Map config rule strings to functions: each returns (transformed_value, target_proto or None)
processors: Dict[str, Callable[[str, str], Tuple[str, str]]] = {
    "map_to_hysteria2": lambda u, p: (u.replace(p, "hysteria2://", 1), "hysteria2"),
}
