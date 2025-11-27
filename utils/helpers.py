import json
import re
from urllib.parse import unquote_plus
from utils.validators import validators_map
from utils.processors import processors_map


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


helpers_map = {
    "write_json_file": write_json_file,
    "parse_params": parse_params,
    "extract_params": extract_params,
    "extract_params_vmess": extract_params_vmess,
}
