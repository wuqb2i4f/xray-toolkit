import json
import re
from urllib.parse import unquote_plus
from utils.validators import validators_map
from utils.processors import processors_map


def validate_object(obj, fields_config):
    for field, field_def in fields_config.items():
        if field not in obj:
            if field_def.get("required", False):
                return False
            continue
        value = obj[field]
        if not validate_field(value, field_def):
            return False
    return True


def validate_field(value, field_def):
    field_type = field_def.get("type", "string")
    if not check_type(value, field_type):
        return False
    if "range" in field_def and field_type == "int":
        if not check_range(value, field_def["range"]):
            return False
    if "allowed" in field_def:
        if not check_allowed(value, field_def["allowed"]):
            return False
    validators = field_def.get("validators", [])
    if not apply_validators(value, validators):
        return False
    return True


def check_type(value, field_type):
    if field_type == "int" and not isinstance(value, int):
        return False
    elif field_type == "string" and not isinstance(value, str):
        return False
    elif field_type == "dict" and not isinstance(value, dict):
        return False
    elif field_type == "list" and not isinstance(value, list):
        return False
    return True


def check_range(value, range_def):
    min_val, max_val = range_def
    return min_val <= value <= max_val


def check_allowed(value, allowed):
    if isinstance(allowed, set):
        return value in allowed
    elif isinstance(allowed, list):
        return value in allowed
    return False


def apply_validators(value, validators):
    if not validators:
        return True
    for validator in validators:
        if validator in validators_map:
            if validators_map[validator](value):
                return True
        else:
            print(
                f"Unknown validator '{validator}' in config - skipping (add to validators_map)."
            )
    return False


def read_raw_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


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
