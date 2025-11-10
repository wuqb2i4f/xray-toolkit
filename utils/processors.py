import base64
from typing import Dict, Callable, Tuple


def map_to_hysteria2(uri: str, prefix: str) -> Tuple[str, str]:
    """Map the URI to a Hysteria2 scheme by replacing the prefix."""
    return (uri.replace(prefix, "hysteria2://", 1), "hysteria2")


def decode_b64_ss(b64_part: str, prefix: str) -> Tuple[str, str]:
    """Decode base64 part to method:password string, targeting 'ss' proto."""
    # Padding for base64 (prefix is ignored here, but kept for signature match)
    b64_padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
    try:
        decoded = base64.b64decode(b64_padded).decode("utf-8").rstrip("\0")
        if ":" not in decoded:
            raise ValueError(f"Invalid decoded content (no ':'): {decoded}")
        method, password = decoded.split(":", 1)
        return (f"{method}:{password}", "ss")
    except (base64.binascii.Error, UnicodeDecodeError, ValueError) as e:
        raise ValueError(f"Invalid base64 part '{b64_part}': {str(e)}")


# Map config rule strings to functions: each returns (transformed_value, target_proto or None)
processors: Dict[str, Callable[[str, str], Tuple[str, str]]] = {
    "map_to_hysteria2": map_to_hysteria2,
    "decode_b64_ss": decode_b64_ss,
}
