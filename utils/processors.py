import base64
from urllib.parse import unquote
from typing import Dict, Any


def map_to_hysteria2(uri: str) -> str:
    """Map the URI to a Hysteria2 scheme by replacing the prefix."""
    uri = uri.replace("hy2://", "hysteria2://", 1)
    return uri


def decode_b64_simple(b64_part: str) -> str:
    """Simple Base64 decode to string, no validation."""
    b64_padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
    decoded = base64.b64decode(b64_padded).decode("utf-8").rstrip("\0")
    return decoded


def decode_remarks(remarks: str) -> str:
    """Process remarks string: iteratively decode URL-encoding if present, otherwise leave as is.
    Handles multi-layer encoding and strips junk.
    """
    current = remarks
    max_iters = 10
    for _ in range(max_iters):
        try:
            decoded = unquote(current)
            decoded = decoded.rstrip("\0")
            if decoded == current:
                return decoded
            current = decoded
        except Exception:
            return remarks
    return current


def case_insensitive_hash(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively normalize string values to lowercase for case-insensitive hashing."""
    normalized = {}
    for k, v in d.items():
        if isinstance(v, str):
            normalized[k] = v.lower()
        elif isinstance(v, dict):
            normalized[k] = case_insensitive_hash(v)
        else:
            normalized[k] = v
    return normalized


# Map config rule strings to functions: each returns (transformed_value, target_proto or None)
processors = {
    "map_to_hysteria2": map_to_hysteria2,
    "decode_b64_simple": decode_b64_simple,
    "decode_remarks": decode_remarks,
    "case_insensitive_hash": case_insensitive_hash,
}
