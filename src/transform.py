import json
import re
import hashlib
from config.config import PROXIES, URIS_RAW_PATH, URIS_TRANSFORM_PATH
from utils.processors import processors_map
from utils.helpers import read_raw_file, write_json_file, parse_params, extract_params


def transform_uris():
    uris = read_raw_file(URIS_RAW_PATH)
    processed_objects = []
    hashes = set()
    for uri in uris:
        if "://" not in uri:
            continue
        protocol_key = uri.split("://")[0]
        if protocol_key not in PROXIES["PROTOCOLS"]:
            print(f"Unknown protocol '{protocol_key}' for URI: {uri} - skipping.")
            continue
        protocol_values = PROXIES["PROTOCOLS"][protocol_key]
        proxy_object = process_protocol(uri, protocol_key, protocol_values)
        proxy_object = process_security(proxy_object, PROXIES["SECURITIES"])
        proxy_object = process_transport(proxy_object, PROXIES["TRANSPORTS"])
        if proxy_object:
            hash = compute_hash(proxy_object)
            proxy_object["hash"] = hash
            if proxy_object["hash"] not in hashes:
                hashes.add(proxy_object["hash"])
                processed_objects.append(proxy_object)
    print(
        f"Processed {len(processed_objects)} unique URIs from {len(uris)} raw (deduplicated {len(uris) - len(processed_objects)} duplicates)."
    )
    write_json_file(processed_objects, URIS_TRANSFORM_PATH)
    return None


def process_protocol(uri, protocol_key, protocol_values):
    parser = parsers_map.get(protocol_key)
    if parser:
        return parser(uri, protocol_values)
    else:
        return None


def parse_vless_uri(uri, protocol_values):
    pattern = r"vless://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    id_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4)
    params = parse_params(query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    uuid = processors_map["id_to_uuid"](id_raw)
    params_protocol = extract_params(params, protocol_values)
    if params_protocol is None:
        return None
    obj = {
        "protocol": {
            "type": "vless",
            "address": address,
            "port": port,
            "id": uuid,
            **params_protocol,
        },
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_trojan_uri(uri, protocol_values):
    pattern = r"trojan://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    password_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = parse_params(query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    params_protocol = extract_params(params, protocol_values)
    if params_protocol is None:
        return None
    obj = {
        "protocol": {
            "type": "trojan",
            "address": address,
            "port": port,
            "password": password_raw,
            **params_protocol,
        },
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_ss_uri(uri, fields_config):
    # """Parse SS URI using small helpers, then validate full object."""
    # # Extract base64, address, port, params, remarks from SS URI regex match.
    # pattern = r"ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    # match = re.match(pattern, uri)
    # if not match:
    #     return None

    # b64_part = match.group(1)
    # address = match.group(2)
    # port_str = match.group(3)
    # params_str = match.group(4) or ""
    # remarks = match.group(5) or ""

    # # Parse port
    # try:
    #     port = int(port_str)
    # except ValueError:
    #     return None

    # # Decode base64 to method:password
    # decode_result = processors_map["decode_b64_simple"](b64_part)
    # if not decode_result:
    #     return None
    # try:
    #     method, password = decode_result.split(":", 1)
    # except ValueError:
    #     return None

    # # Parse params and remarks
    # decoded_params = processors_map["decode_url_encode"](params_str)
    # params = parse_params(decoded_params)
    # decoded_remarks = processors_map["decode_url_encode"](remarks)

    # # Build object
    # obj = {
    #     "address": address,
    #     "port": port,
    #     "method": method,
    #     "password": password,
    #     "keys": params,
    #     "remarks": decoded_remarks,
    # }

    # # Compute and add config_hash
    # config_hash = compute_hash(obj)
    # obj["config_hash"] = config_hash

    # # Validate
    # if not validate_object(obj, fields_config):
    #     return None

    # return obj
    return None


def parse_vmess_uri(uri, fields_config):
    # """Parse VMess URI: detect format and delegate to appropriate parser."""
    # # Try base64 JSON format first (most common)
    # pattern_b64 = r"vmess://([^#]+)$"
    # if re.match(pattern_b64, uri):
    #     return parse_vmess_b64_format(uri, fields_config)

    # # If not, try URI format (similar to VLESS)
    # pattern_uri = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    # if re.match(pattern_uri, uri):
    #     return parse_vmess_uri_format(uri, fields_config)

    # # Neither format matched
    return None


def parse_vmess_b64_format(uri, fields_config):
    # """Parse VMess base64 JSON format."""
    # # Extract base64 part and remarks
    # pattern = r"vmess://([^#]+)$"
    # match = re.match(pattern, uri)
    # if not match:
    #     return None

    # b64_part = match.group(1)

    # # Decode base64 to JSON string
    # json_str = processors_map["decode_b64_simple"](b64_part)
    # if not json_str:
    #     return None

    # # Parse JSON
    # try:
    #     obj_data = json.loads(json_str)
    # except json.JSONDecodeError:
    #     return None

    # # Extract core fields
    # address = obj_data.get("add", "")
    # port_obj = obj_data.get("port")
    # id = obj_data.get("id", "")
    # remarks = obj_data.get("ps", "")

    # if not address or port_obj is None or not id:
    #     return None

    # # Parse port
    # try:
    #     port = int(port_obj)
    # except ValueError:
    #     return None

    # # Process ID to UUID
    # uuid = processors_map["id_to_uuid"](id)

    # # Extract all other fields into 'keys' (excluding address/add, port, id, ps/remarks)
    # excluded_keys = {"add", "port", "id", "ps", "v", "aid"}
    # keys = {}
    # for key, value in obj_data.items():
    #     if key not in excluded_keys and value is not None and str(value) != "":
    #         keys[key] = value

    # # Build object
    # obj = {
    #     "address": address,
    #     "port": port,
    #     "id": uuid,
    #     "keys": keys,
    #     "remarks": remarks,
    # }

    # # Compute and add config_hash
    # config_hash = compute_hash(obj)
    # obj["config_hash"] = config_hash

    # # Validate
    # if not validate_object(obj, fields_config):
    #     return None

    # return obj
    return None


def parse_vmess_uri_format(uri, fields_config):
    # """Parse VMESS URI using small helpers, then validate full object."""
    # # Extract id, address, port, params, remarks from VMESS URI regex match.
    # pattern = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    # match = re.match(pattern, uri)
    # if not match:
    #     return None

    # id = match.group(1)
    # address = match.group(2)
    # port_str = match.group(3)
    # params_str = match.group(4) or ""
    # remarks = match.group(5) or ""

    # # Parse port
    # try:
    #     port = int(port_str)
    # except ValueError:
    #     return None

    # # Parse params and remarks
    # decode_id = processors_map["decode_url_encode"](id)
    # uuid = processors_map["id_to_uuid"](decode_id)
    # decoded_params = processors_map["decode_url_encode"](params_str)
    # params = parse_params(decoded_params)
    # decoded_remarks = processors_map["decode_url_encode"](remarks)

    # # Build object
    # obj = {
    #     "address": address,
    #     "port": port,
    #     "id": uuid,
    #     "keys": params,
    #     "remarks": decoded_remarks,
    # }

    # # Compute and add config_hash
    # config_hash = compute_hash(obj)
    # obj["config_hash"] = config_hash

    # # Validate
    # if not validate_object(obj, fields_config):
    #     return None

    # return obj
    return None


def parse_hysteria2_uri(uri, fields_config):
    # """Parse Hysteria2 URI using small helpers, then validate full object."""
    # # Extract password, address, port, params, remarks from Hysteria2 URI regex match.
    # pattern = r"hysteria2://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    # match = re.match(pattern, uri)
    # if not match:
    #     return None

    # password = match.group(1)
    # address = match.group(2)
    # port_str = match.group(3)
    # params_str = match.group(4) or ""
    # remarks = match.group(5) or ""

    # # Parse port
    # try:
    #     port = int(port_str)
    # except ValueError:
    #     return None

    # # Parse params and remarks
    # decoded_params = processors_map["decode_url_encode"](params_str)
    # params = parse_params(decoded_params)
    # decoded_remarks = processors_map["decode_url_encode"](remarks)

    # # Build object
    # obj = {
    #     "address": address,
    #     "port": port,
    #     "password": password,
    #     "keys": params,
    #     "remarks": decoded_remarks,
    # }

    # # Compute and add config_hash
    # config_hash = compute_hash(obj)
    # obj["config_hash"] = config_hash

    # # Validate
    # if not validate_object(obj, fields_config):
    #     return None

    # return obj
    return None


def compute_hash(obj):
    hash_input = {k: v for k, v in obj.items()}
    hash_input = processors_map["case_insensitive_hash"](hash_input)
    hash_string = json.dumps(hash_input, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(hash_string.encode("utf-8"))
    return hash_obj.hexdigest()


def process_security(proxy_object, securities):
    if not proxy_object:
        return None
    params = proxy_object.get("params", {})
    security_raw = params.get("security", "").strip().lower()
    if not security_raw or security_raw not in securities:
        security_type = "none"
    else:
        security_type = security_raw
    security_obj = {"type": security_type}
    if security_type != "none":
        security_values = securities[security_type]
        security_params = extract_params(params, security_values)
        if security_params is None:
            return None
        security_obj = {**security_obj, **security_params}
    proxy_object["security"] = security_obj
    return proxy_object


def process_transport(proxy_object, transports):
    if not proxy_object:
        return None
    params = proxy_object.get("params", {})
    transport_raw = params.get("type", "").strip().lower()
    if not transport_raw or transport_raw not in transports:
        transport_type = "raw"
    else:
        transport_type = transport_raw
    transport_obj = {"type": transport_type}
    transport_values = transports[transport_type]
    tarnsport_params = extract_params(params, transport_values)
    if tarnsport_params is None:
        return None
    transport_obj = {**transport_obj, **tarnsport_params}
    proxy_object["transport"] = transport_obj
    return proxy_object


parsers_map = {
    "vless": parse_vless_uri,
    "trojan": parse_trojan_uri,
    "ss": parse_ss_uri,
    "vmess": parse_vmess_uri,
    "hysteria2": parse_hysteria2_uri,
}


# For testing
if __name__ == "__main__":
    transform_uris()
