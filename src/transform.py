import json
import re
import hashlib
from typing import Dict, List, Any
from config.config import PROXIES
from utils.helpers import validate_object
from utils.processors import processors_map


def transform_uris() -> None:
    """
    Orchestrate transform: Read raw files, process URIs per protocol, write JSON array to processed.
    """
    for proto, config in PROXIES["PROTOCOLS"].items():
        uri_config = config.get("uri", {})
        raw_path = uri_config.get("raw_output")
        processed_path = uri_config.get("processed_output")
        fields_config = config.get("fields", {})
        if not raw_path or not processed_path or not fields_config:
            print(f"No fields config for {proto} - skipping.")
            continue

        try:
            uris = read_raw_file(raw_path)
            processed_objects = process_uris(uris, proto, fields_config)
            write_json_file(processed_objects, processed_path, proto)
        except FileNotFoundError:
            print(f"Raw file not found: {raw_path} - skipping {proto}")
            continue

    print("Transform complete for all protocols.")
    return None


def read_raw_file(file_path: str) -> List[str]:
    """Read URIs from raw file, one per line."""
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def process_uris(
    uris: List[str], proto: str, fields_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Validate and parse URIs using fields config; return list of unique dicts by config_hash."""
    processed = []
    seen_hashes = set()
    for uri in uris:
        obj = parse_and_validate_uri(uri, proto, fields_config)
        if obj and "config_hash" in obj:
            if obj["config_hash"] not in seen_hashes:
                seen_hashes.add(obj["config_hash"])
                processed.append(obj)
    print(
        f"Processed {len(processed)} unique {proto} URIs from {len(uris)} raw (deduplicated {len(uris) - len(processed)} duplicates)."
    )
    return processed


def parse_and_validate_uri(
    uri: str, proto: str, fields_config: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Parse URI to dict based on protocol, validate using fields config."""
    if proto == "vless":
        return parse_vless_uri(uri, fields_config)
    elif proto == "trojan":
        return parse_trojan_uri(uri, fields_config)
    elif proto == "ss":
        return parse_ss_uri(uri, fields_config)
    elif proto == "vmess":
        return parse_vmess_uri(uri, fields_config)
    elif proto == "hysteria2":
        return parse_hysteria2_uri(uri, fields_config)
    # Placeholder for other protocols
    else:
        print(f"No parser for {proto} yet - skipping.")
        return None


def parse_params(params_str: str) -> Dict[str, str]:
    """Parse query params from string into a dict."""
    params = {}
    if params_str:
        # Split on either & or ; as separators
        pairs = re.split(r"[&;]", params_str)
        for pair in pairs:
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v
    return params


def compute_config_hash(obj: Dict[str, Any]) -> str:
    """Compute SHA256 hash from all fields except 'remarks' (case-insensitive)."""
    hash_input = {k: v for k, v in obj.items() if k not in ["remarks"]}
    hash_input = processors_map["case_insensitive_hash"](hash_input)
    hash_string = json.dumps(hash_input, sort_keys=True)
    hash_obj = hashlib.sha256(hash_string.encode("utf-8"))
    return hash_obj.hexdigest()


def parse_vless_uri(uri: str, fields_config: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse VLESS URI using small helpers, then validate full object."""
    # Extract id, address, port, params, remarks from VLESS URI regex match.
    pattern = r"vless://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    id = match.group(1)
    address = match.group(2)
    port_str = match.group(3)
    params_str = match.group(4) or ""
    remarks = match.group(5) or ""

    # Parse port
    try:
        port = int(port_str)
    except ValueError:
        return None

    # Parse params and remarks
    decode_id = processors_map["decode_url_encode"](id)
    uuid = processors_map["id_to_uuid"](decode_id)
    decoded_params = processors_map["decode_url_encode"](params_str)
    params = parse_params(decoded_params)
    decoded_remarks = processors_map["decode_url_encode"](remarks)

    # Build object
    obj = {
        "address": address,
        "port": port,
        "id": uuid,
        "keys": params,
        "remarks": decoded_remarks,
    }

    # Compute and add config_hash
    config_hash = compute_config_hash(obj)
    obj["config_hash"] = config_hash

    # Validate
    if not validate_object(obj, fields_config):
        return None

    return obj


def parse_trojan_uri(uri: str, fields_config: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse Trojan URI using small helpers, then validate full object."""
    # Extract password, address, port, params, remarks from Trojan URI regex match.
    pattern = r"trojan://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    password = match.group(1)
    address = match.group(2)
    port_str = match.group(3)
    params_str = match.group(4) or ""
    remarks = match.group(5) or ""

    # Parse port
    try:
        port = int(port_str)
    except ValueError:
        return None

    # Parse params and remarks
    decode_password = processors_map["decode_url_encode"](password)
    decoded_params = processors_map["decode_url_encode"](params_str)
    params = parse_params(decoded_params)
    decoded_remarks = processors_map["decode_url_encode"](remarks)

    # Build object
    obj = {
        "address": address,
        "port": port,
        "password": decode_password,
        "keys": params,
        "remarks": decoded_remarks,
    }

    # Compute and add config_hash
    config_hash = compute_config_hash(obj)
    obj["config_hash"] = config_hash

    # Validate
    if not validate_object(obj, fields_config):
        return None

    return obj


def parse_ss_uri(uri: str, fields_config: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse SS URI using small helpers, then validate full object."""
    # Extract base64, address, port, params, remarks from SS URI regex match.
    pattern = r"ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    b64_part = match.group(1)
    address = match.group(2)
    port_str = match.group(3)
    params_str = match.group(4) or ""
    remarks = match.group(5) or ""

    # Parse port
    try:
        port = int(port_str)
    except ValueError:
        return None

    # Decode base64 to method:password
    decode_result = processors_map["decode_b64_simple"](b64_part)
    if not decode_result:
        return None
    try:
        method, password = decode_result.split(":", 1)
    except ValueError:
        return None

    # Parse params and remarks
    decoded_params = processors_map["decode_url_encode"](params_str)
    params = parse_params(decoded_params)
    decoded_remarks = processors_map["decode_url_encode"](remarks)

    # Build object
    obj = {
        "address": address,
        "port": port,
        "method": method,
        "password": password,
        "keys": params,
        "remarks": decoded_remarks,
    }

    # Compute and add config_hash
    config_hash = compute_config_hash(obj)
    obj["config_hash"] = config_hash

    # Validate
    if not validate_object(obj, fields_config):
        return None

    return obj


def parse_vmess_uri(uri: str, fields_config: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse VMess URI: detect format and delegate to appropriate parser."""
    # Try base64 JSON format first (most common)
    pattern_b64 = r"vmess://([^#]+)$"
    if re.match(pattern_b64, uri):
        return parse_vmess_b64_format(uri, fields_config)

    # If not, try URI format (similar to VLESS)
    pattern_uri = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    if re.match(pattern_uri, uri):
        return parse_vmess_uri_format(uri, fields_config)

    # Neither format matched
    return None


def parse_vmess_b64_format(
    uri: str, fields_config: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Parse VMess base64 JSON format."""
    # Extract base64 part and remarks
    pattern = r"vmess://([^#]+)(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    b64_part = match.group(1)
    raw_remarks = match.group(2) or ""
    decoded_remarks = processors_map["decode_url_encode"](raw_remarks)

    # Decode base64 to JSON string
    json_str = processors_map["decode_b64_simple"](b64_part)
    if not json_str:
        return None

    # Parse JSON
    try:
        obj_data = json.loads(json_str)
    except json.JSONDecodeError:
        return None

    # Extract core fields
    address = obj_data.get("add", "")
    port_obj = obj_data.get("port")
    id = obj_data.get("id", "")

    if not address or port_obj is None or not id:
        return None

    # Parse port
    try:
        port = int(port_obj)
    except ValueError:
        return None

    # Process ID to UUID
    uuid = processors_map["id_to_uuid"](id)

    # Extract additional fields for keys
    aid = obj_data.get("aid", 0)
    net = obj_data.get("net", "")
    type_ = obj_data.get("type", "")  # header type
    host = obj_data.get("host", "")
    path = obj_data.get("path", "")
    tls = obj_data.get("tls", "")

    # Use #remarks if present, otherwise fall back to "ps"
    final_remarks = decoded_remarks or obj_data.get("ps", "")

    # Build keys dict
    keys = {
        "aid": aid,
        "net": net,
        "type": type_,
        "host": host,
        "path": path,
        "tls": tls,
    }
    # Remove empty values
    keys = {k: v for k, v in keys.items() if v is not None and str(v).strip() != ""}

    # Build object
    obj = {
        "address": address,
        "port": port,
        "id": uuid,
        "keys": keys,
        "remarks": final_remarks,
    }

    # Compute and add config_hash
    config_hash = compute_config_hash(obj)
    obj["config_hash"] = config_hash

    # Validate
    if not validate_object(obj, fields_config):
        return None

    return obj


def parse_vmess_uri_format(
    uri: str, fields_config: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Parse VMESS URI using small helpers, then validate full object."""
    # Extract id, address, port, params, remarks from VMESS URI regex match.
    pattern = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    id = match.group(1)
    address = match.group(2)
    port_str = match.group(3)
    params_str = match.group(4) or ""
    remarks = match.group(5) or ""

    # Parse port
    try:
        port = int(port_str)
    except ValueError:
        return None

    # Parse params and remarks
    decode_id = processors_map["decode_url_encode"](id)
    uuid = processors_map["id_to_uuid"](decode_id)
    decoded_params = processors_map["decode_url_encode"](params_str)
    params = parse_params(decoded_params)
    decoded_remarks = processors_map["decode_url_encode"](remarks)

    # Build object
    obj = {
        "address": address,
        "port": port,
        "id": uuid,
        "keys": params,
        "remarks": decoded_remarks,
    }

    # Compute and add config_hash
    config_hash = compute_config_hash(obj)
    obj["config_hash"] = config_hash

    # Validate
    if not validate_object(obj, fields_config):
        return None

    return obj


def parse_hysteria2_uri(
    uri: str, fields_config: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Parse Hysteria2 URI using small helpers, then validate full object."""
    # Extract password, address, port, params, remarks from Hysteria2 URI regex match.
    pattern = r"hysteria2://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    password = match.group(1)
    address = match.group(2)
    port_str = match.group(3)
    params_str = match.group(4) or ""
    remarks = match.group(5) or ""

    # Parse port
    try:
        port = int(port_str)
    except ValueError:
        return None

    # Parse params and remarks
    decoded_params = processors_map["decode_url_encode"](params_str)
    params = parse_params(decoded_params)
    decoded_remarks = processors_map["decode_url_encode"](remarks)

    # Build object
    obj = {
        "address": address,
        "port": port,
        "password": password,
        "keys": params,
        "remarks": decoded_remarks,
    }

    # Compute and add config_hash
    config_hash = compute_config_hash(obj)
    obj["config_hash"] = config_hash

    # Validate
    if not validate_object(obj, fields_config):
        return None

    return obj


def write_json_file(objects: List[Dict[str, Any]], file_path: str, proto: str) -> None:
    """Write list of dicts as JSON array to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON with {len(objects)} processed {proto} URIs to {file_path}.")


# For testing
if __name__ == "__main__":
    transform_uris()
