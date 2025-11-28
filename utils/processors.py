import base64
import json
import re
import uuid
from urllib.parse import unquote, unquote_plus
from utils.validators import validators_map


def to_hysteria2(uri):
    uri = uri.replace("hy2://", "hysteria2://", 1)
    return uri


def decode_b64_simple(b64_part):
    if not b64_part:
        return None
    valid_b64 = re.sub(r"[^A-Za-z0-9+/=_\-]", "", b64_part)
    if not valid_b64:
        return None
    valid_b64 = valid_b64.replace("-", "+").replace("_", "/")
    padded = valid_b64 + "=" * ((4 - len(valid_b64) % 4) % 4)
    try:
        data = base64.b64decode(padded)
        decoded = data.decode("utf-8").rstrip("\0")
        return decoded
    except Exception:
        return None


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


def to_lower(s) -> str:
    if s is None:
        return None
    if isinstance(s, str):
        return s.lower()
    try:
        return str(s).lower()
    except Exception:
        return str(s)


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


def path_start_with_slash(value):
    if isinstance(value, str):
        if not value.startswith("/"):
            return "/" + value
        return value
    elif isinstance(value, list):
        normalized = []
        for p in value:
            if isinstance(p, str) and not p.startswith("/"):
                normalized.append("/" + p)
            else:
                normalized.append(p)
        return normalized
    return value


def uri_generator(file_path):
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            uri = line.strip()
            if uri:
                yield {"uri": uri}


def write_json_file(objects, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON with {len(objects)} processed URIs to {file_path}.")


def parse_params(params_str):
    params = {}
    if params_str:
        pairs = re.split(r"[&;]", params_str)
        for pair in pairs:
            if "=" in pair:
                k, v = pair.split("=", 1)
                v = (
                    v.replace("True", "true")
                    .replace("False", "false")
                    .replace("None", "none")
                )
                if v.startswith("{") and v.endswith("}"):
                    k = unquote_plus(k)
                    v = unquote_plus(v)
                    k = k.replace("'", '"')
                    v = v.replace("'", '"')
                    try:
                        params[k] = json.loads(v)
                    except json.JSONDecodeError:
                        params[k] = v
                else:
                    params[k] = v
    return params


def extract_params(params, field_values):
    if not isinstance(field_values, dict):
        return None
    result = {}
    for field_key, field_value in field_values.items():
        if not isinstance(field_value, dict):
            continue
        source = field_value.get("source")
        default = field_value.get("default")
        required = field_value.get("required", True)
        processors_list = field_value.get("processors", [])
        validators = field_value.get("validators", [])
        if source != "params":
            continue
        raw_value = params.get(field_key)
        if raw_value is None:
            if default is not None:
                result[field_key] = default
            elif required:
                return None
            continue
        else:
            for rule in processors_list:
                if rule in processors_map:
                    raw_value = processors_map[rule](raw_value)
            for validator_name in validators:
                validator_func = validators_map.get(validator_name)
                if validator_func:
                    if not validator_func(raw_value):
                        return None
            result[field_key] = raw_value
    result = {k: v for k, v in result.items() if v != ""}
    return result if result else None


def extract_params_vmess(obj_data):
    excluded_keys = {"add", "port", "id", "ps", "v", "aid", "skip-cert-verify"}
    params = {}
    for key, value in obj_data.items():
        if key not in excluded_keys and value is not None and str(value) != "":
            if key == "scy":
                new_key = "encryption"
            elif key == "tls":
                new_key = "security"
            elif key == "type":
                new_key = "headerType"
            elif key == "net":
                new_key = "type"
            else:
                new_key = key
            params[new_key] = value
    return params


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
    "path_start_with_slash": path_start_with_slash,
    "uri_generator": uri_generator,
    "write_json_file": write_json_file,
    "parse_params": parse_params,
    "extract_params": extract_params,
    "extract_params_vmess": extract_params_vmess,
}
