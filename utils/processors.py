import base64
import uuid
from urllib.parse import unquote
from utils.validators import validators_map


def to_hysteria2(uri):
    uri = uri.replace("hy2://", "hysteria2://", 1)
    return uri


def decode_b64_simple(b64_part):
    b64_padded = b64_part + "=" * ((4 - len(b64_part) % 4) % 4)
    decoded = base64.b64decode(b64_padded).decode("utf-8").rstrip("\0")
    return decoded


def decode_url_encode(misc_string):
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
    if id_str and not validators_map["uuid"](id_str):
        namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
        generated_uuid = uuid.uuid5(namespace, id_str)
        return str(generated_uuid)
    return id_str


def to_lower(s):
    return s.lower() if s else ""


def to_int(s):
    try:
        return int(s)
    except ValueError:
        return None


def split_method_password(decoded):
    if ":" in decoded:
        return decoded.split(":", 1)
    return decoded, ""


def split_comma_to_list(s):
    if s:
        return [x.strip() for x in s.split(",")]
    return []


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
