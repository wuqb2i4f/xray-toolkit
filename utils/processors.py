import base64
import uuid
from urllib.parse import unquote
from utils.validators import validators_map


def to_hysteria2(uri):
    """Map the URI to a Hysteria2 scheme by replacing the prefix."""
    uri = uri.replace("hy2://", "hysteria2://", 1)
    return uri


def decode_b64_simple(b64_part):
    """Simple Base64 decode to string, no validation."""
    b64_padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
    decoded = base64.b64decode(b64_padded).decode("utf-8").rstrip("\0")
    return decoded


def decode_url_encode(misc_string):
    """Process string: iteratively decode URL-encoding if present, otherwise leave as is.
    Handles multi-layer encoding and strips junk.
    """
    current = misc_string
    while True:
        try:
            decoded = unquote(current)
            decoded = decoded.rstrip("\0")
            if decoded == current:
                return decoded
            current = decoded
        except Exception:
            return misc_string


def case_insensitive_hash(d):
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


def id_to_uuid(id_str):
    """Convert input ID to UUID: return as-is if valid UUID, else generate UUIDv5 from nil namespace."""
    if id_str and not validators_map["uuid"](id_str):
        namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
        generated_uuid = uuid.uuid5(namespace, id_str)
        return str(generated_uuid)
    return id_str


def to_lower(s):
    """Convert string to lowercase, return empty if None/empty."""
    return s.lower() if s else ""


def to_int(s):
    """Convert string to int, return None if invalid."""
    try:
        return int(s)
    except ValueError:
        return None


def split_method_password(decoded):
    """Split decoded SS b64 string 'method:password' into (method, password)."""
    if ":" in decoded:
        return decoded.split(":", 1)
    return decoded, ""


def split_comma_to_list(s):
    """Split comma-separated string to list, strip whitespace."""
    if s:
        return [x.strip() for x in s.split(",")]
    return []


# Map config rule strings to functions: each returns (transformed_value, target_proto or None)
processors_map = {
    "to_hysteria2": to_hysteria2,
    "decode_b64_simple": decode_b64_simple,
    "decode_url_encode": decode_url_encode,
    "case_insensitive_hash": case_insensitive_hash,
    "id_to_uuid": id_to_uuid,
    "to_lower": to_lower,
    "to_int": to_int,
    "split_method_password": split_method_password,
    "split_comma_to_list": split_comma_to_list,
}
