from typing import Dict, Callable, Tuple


def map_to_hysteria2(uri: str, prefix: str) -> Tuple[str, str]:
    """Map the URI to a Hysteria2 scheme by replacing the prefix."""
    return (uri.replace(prefix, "hysteria2://", 1), "hysteria2")


# Map config rule strings to functions: each returns (transformed_value, target_proto or None)
processors: Dict[str, Callable[[str, str], Tuple[str, str]]] = {
    "map_to_hysteria2": map_to_hysteria2,
}
