import json
import re
import hashlib


def transform_uris(configs_map, processors_map, helpers_map, database_map):
    db_path = configs_map["DB_PATH"]
    uris_transform_path = configs_map["URIS_TRANSFORM_PATH"]
    protocols_object = configs_map["PROXIES"]["PROTOCOLS"]
    securities_object = configs_map["PROXIES"]["SECURITIES"]
    transports_object = configs_map["PROXIES"]["TRANSPORTS"]
    raw_records = database_map["select_all"](
        db_path, "uris_raw", where_clause="processed = 0", params=()
    )
    uris = [row["uri"] for row in raw_records]
    print(f"Loaded {len(uris)} unprocessed URIs from database.")
    processed_objects = []
    seen_hashes = set()
    uri_to_hash = {}
    uri_to_processed = {}
    for uri in uris:
        if "://" not in uri:
            uri_to_processed[uri] = 1
            continue
        protocol_key = uri.split("://")[0]
        if protocol_key not in protocols_object:
            uri_to_processed[uri] = 1
            continue
        proxy_object = process_protocol(
            uri,
            protocol_key,
            protocols_object[protocol_key],
            processors_map,
            helpers_map,
        )
        proxy_object = process_security(proxy_object, securities_object, helpers_map)
        proxy_object = process_transport(
            proxy_object, transports_object, processors_map, helpers_map
        )
        if not proxy_object:
            uri_to_processed[uri] = 1
            continue
        proxy_object.pop("params", None)
        hash_val = compute_hash(proxy_object, processors_map)
        proxy_object["hash"] = hash_val
        uri_to_processed[uri] = 1
        if hash_val not in seen_hashes:
            seen_hashes.add(hash_val)
            processed_objects.append(proxy_object)
            uri_to_hash[uri] = hash_val
        else:
            uri_to_processed[uri] = 1
    helpers_map["write_json_file"](processed_objects, uris_transform_path)
    if uri_to_processed:
        database_map["bulk_update_multi_columns"](
            db_path=db_path,
            table_name="uris_raw",
            updates={uri: {"processed": 1} for uri in uri_to_processed.keys()},
            key_column="uri",
            extra_sets={"updated_at": "CURRENT_TIMESTAMP"},
        )
    if uri_to_hash:
        database_map["bulk_update_multi_columns"](
            db_path=db_path,
            table_name="uris_raw",
            updates={uri: {"hash": h} for uri, h in uri_to_hash.items()},
            key_column="uri",
            extra_sets={"updated_at": "CURRENT_TIMESTAMP"},
        )
    print(f"   → {len(processed_objects)} unique configs saved to JSON")
    print(f"   → {len(uri_to_processed)} URIs marked as processed")
    print(f"   → {len(uri_to_hash)} URIs got a unique hash")
    print(f"   → {len(uris) - len(uri_to_processed)} failed/skipped")


def process_protocol(uri, protocol_key, protocol_values, processors_map, helpers_map):
    parser = parsers_map.get(protocol_key)
    if parser:
        return parser(uri, protocol_values, processors_map, helpers_map)
    else:
        return None


def parse_vless_uri(uri, protocol_values, processors_map, helpers_map):
    pattern = r"vless://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    id_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4)
    params = helpers_map["parse_params"](query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    uuid = processors_map["id_to_uuid"](id_raw)
    params_protocol = helpers_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "vless",
        "address": address,
        "port": port,
        "id": uuid,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_trojan_uri(uri, protocol_values, processors_map, helpers_map):
    pattern = r"trojan://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    password_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = helpers_map["parse_params"](query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    params_protocol = helpers_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "trojan",
        "address": address,
        "port": port,
        "password": password_raw,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_ss_uri(uri, protocol_values, processors_map, helpers_map):
    pattern = r"ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    b64_part_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = helpers_map["parse_params"](query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    b64_part_decode = processors_map["decode_b64_simple"](b64_part_raw)
    if not b64_part_decode:
        return None
    try:
        method, password = b64_part_decode.split(":", 1)
    except ValueError:
        return None
    params_protocol = helpers_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "ss",
        "address": address,
        "port": port,
        "method": method,
        "password": password,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_vmess_uri(uri, protocol_values, processors_map, helpers_map):
    pattern_b64 = r"vmess://([^#]+)$"
    if re.match(pattern_b64, uri):
        return parse_vmess_b64_format(uri, protocol_values, processors_map, helpers_map)
    pattern_uri = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    if re.match(pattern_uri, uri):
        return parse_vmess_uri_format(uri, protocol_values, processors_map, helpers_map)
    return None


def parse_vmess_b64_format(uri, protocol_values, processors_map, helpers_map):
    pattern = r"vmess://([^#]+)$"
    match = re.match(pattern, uri)
    if not match:
        return None
    b64_part_raw = match.group(1)
    b64_part_decode = processors_map["decode_b64_simple"](b64_part_raw)
    if not b64_part_decode:
        return None
    try:
        obj_data = json.loads(b64_part_decode)
    except json.JSONDecodeError:
        return None
    address_raw = obj_data.get("add", "")
    port_raw = obj_data.get("port")
    id_raw = obj_data.get("id", "")
    if not address_raw or port_raw is None or not id_raw:
        return None
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    uuid = processors_map["id_to_uuid"](id_raw)
    params = helpers_map["extract_params_vmess"](obj_data)
    params_protocol = helpers_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "vmess",
        "address": address,
        "port": port,
        "id": uuid,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_vmess_uri_format(uri, protocol_values, processors_map, helpers_map):
    pattern = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    id_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = helpers_map["parse_params"](query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    uuid = processors_map["id_to_uuid"](id_raw)
    params_protocol = helpers_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "vmess",
        "address": address,
        "port": port,
        "id": uuid,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
    }
    return obj


def parse_hysteria2_uri(uri, protocol_values, processors_map, helpers_map):
    pattern = r"hysteria2://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    password_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = helpers_map["parse_params"](query_raw)
    address = processors_map["to_lower"](address_raw)
    port = processors_map["to_int"](port_raw)
    params_protocol = helpers_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "hysteria2",
        "address": address,
        "port": port,
        "password": password_raw,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    obj = {
        "protocol": protocol_dict,
        "params": params,
    }
    return obj


def compute_hash(obj, processors_map):
    hash_input = {k: v for k, v in obj.items()}
    hash_input = processors_map["case_insensitive_hash"](hash_input)
    hash_string = json.dumps(hash_input, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(hash_string.encode("utf-8"))
    return hash_obj.hexdigest()


def process_security(proxy_object, securities, helpers_map):
    if not proxy_object:
        return None
    if proxy_object.get("security") != {}:
        return proxy_object
    params = proxy_object.get("params", {})
    security_raw = str(params.get("security", "")).strip().lower()
    if not security_raw or security_raw not in securities:
        security_type = "none"
    else:
        security_type = security_raw
    security_obj = {"type": security_type}
    if security_type != "none":
        security_values = securities[security_type]
        security_params = helpers_map["extract_params"](params, security_values)
        if security_params is None:
            return None
        security_obj = {**security_obj, **security_params}
    proxy_object["security"] = security_obj
    return proxy_object


def process_transport(proxy_object, transports, processors_map, helpers_map):
    if not proxy_object:
        return None
    if proxy_object.get("transport") != {}:
        return proxy_object
    params = proxy_object.get("params", {})
    transport_raw = str(params.get("type", "")).strip().lower()
    if not transport_raw or transport_raw not in transports:
        transport_type = "raw"
    else:
        transport_type = transport_raw
    transport_obj = {"type": transport_type}
    transport_values = transports[transport_type]
    tarnsport_params = helpers_map["extract_params"](params, transport_values)
    if tarnsport_params is None:
        return None
    transport_obj = {**transport_obj, **tarnsport_params}
    if transport_type == "raw":
        host_condition = (
            "host" in transport_obj and str(transport_obj["host"]).strip() != ""
        )
        path_condition = (
            "path" in transport_obj
            and isinstance(transport_obj["path"], list)
            and len(transport_obj["path"]) > 0
            and not transport_obj["path"][0] == "/"
        )
        if host_condition or path_condition:
            transport_obj["headerType"] = "http"
    if "path" in transport_obj:
        transport_obj["path"] = processors_map["path_start_with_slash"](
            transport_obj["path"]
        )
    if transport_type == "raw" and transport_obj.get("headerType", "") != "http":
        transport_obj["headerType"] = "none"
        transport_obj.pop("path", None)
        transport_obj.pop("host", None)
    proxy_object["transport"] = transport_obj
    return proxy_object


parsers_map = {
    "vless": parse_vless_uri,
    "trojan": parse_trojan_uri,
    "ss": parse_ss_uri,
    "vmess": parse_vmess_uri,
    "hysteria2": parse_hysteria2_uri,
}
