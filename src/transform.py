import json
import re
import hashlib


def transform_uris(ctx):
    uris_transform_path = ctx.configs_map["URIS_TRANSFORM_PATH"]
    protocols_object = ctx.configs_map["PROXIES"]["PROTOCOLS"]
    db_path = ctx.configs_map["DB_PATH"]
    raw_records = ctx.database_map["select_all"](
        db_path=db_path, table_name="uris_raw", where_clause="processed = 0", params=()
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
            ctx,
        )
        proxy_object = process_security(proxy_object, ctx)
        proxy_object = process_transport(proxy_object, ctx)
        if not proxy_object:
            uri_to_processed[uri] = 1
            continue
        proxy_object.pop("params", None)
        hash_val = compute_hash(proxy_object, ctx)
        proxy_object["hash"] = hash_val
        uri_to_processed[uri] = 1
        if hash_val not in seen_hashes:
            seen_hashes.add(hash_val)
            processed_objects.append(proxy_object)
            uri_to_hash[uri] = hash_val
        else:
            uri_to_processed[uri] = 1
    ctx.processors_map["write_json_file"](processed_objects, uris_transform_path)
    if uri_to_processed:
        ctx.database_map["bulk_upsert"](
            db_path=db_path,
            table_name="uris_raw",
            records=[{"uri": uri, "processed": 1} for uri in uri_to_processed.keys()],
            key_columns="uri",
        )
    if uri_to_hash:
        ctx.database_map["bulk_upsert"](
            db_path=db_path,
            table_name="uris_raw",
            records=[
                {"uri": uri, "processed": 1, "hash": h}
                for uri, h in uri_to_hash.items()
            ],
            key_columns="uri",
        )
    print(f"   → {len(processed_objects)} unique configs saved to JSON")
    print(f"   → {len(uri_to_processed)} URIs marked as processed")
    print(f"   → {len(uri_to_hash)} URIs got a unique hash")
    print(f"   → {len(uris) - len(uri_to_processed)} failed/skipped")


def process_protocol(uri, protocol_key, protocol_values, ctx):
    parser = parsers_map.get(protocol_key)
    if parser:
        return parser(uri, protocol_values, ctx)
    else:
        return None


def parse_vless_uri(uri, protocol_values, ctx):
    pattern = r"vless://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    id_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4)
    params = ctx.processors_map["parse_params"](query_raw)
    address = ctx.processors_map["to_lower"](address_raw)
    port = ctx.processors_map["to_int"](port_raw)
    uuid = ctx.processors_map["id_to_uuid"](id_raw)
    params_protocol = ctx.processors_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "vless",
        "address": address,
        "port": port,
        "id": uuid,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    remarks = protocol_dict["type"][:2]
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
        "remarks": remarks,
    }
    return obj


def parse_trojan_uri(uri, protocol_values, ctx):
    pattern = r"trojan://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    password_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = ctx.processors_map["parse_params"](query_raw)
    address = ctx.processors_map["to_lower"](address_raw)
    port = ctx.processors_map["to_int"](port_raw)
    params_protocol = ctx.processors_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "trojan",
        "address": address,
        "port": port,
        "password": password_raw,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    remarks = protocol_dict["type"][:2]
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
        "remarks": remarks,
    }
    return obj


def parse_ss_uri(uri, protocol_values, ctx):
    pattern = r"ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    b64_part_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = ctx.processors_map["parse_params"](query_raw)
    address = ctx.processors_map["to_lower"](address_raw)
    port = ctx.processors_map["to_int"](port_raw)
    b64_part_decode = ctx.processors_map["decode_b64_simple"](b64_part_raw)
    if not b64_part_decode:
        return None
    try:
        method, password = b64_part_decode.split(":", 1)
    except ValueError:
        return None
    params_protocol = ctx.processors_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "ss",
        "address": address,
        "port": port,
        "method": method,
        "password": password,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    remarks = protocol_dict["type"][:2]
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
        "remarks": remarks,
    }
    return obj


def parse_vmess_uri(uri, protocol_values, ctx):
    pattern_b64 = r"vmess://([^#]+)$"
    if re.match(pattern_b64, uri):
        return parse_vmess_b64_format(uri, protocol_values, ctx)
    pattern_uri = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    if re.match(pattern_uri, uri):
        return parse_vmess_uri_format(uri, protocol_values, ctx)
    return None


def parse_vmess_b64_format(uri, protocol_values, ctx):
    pattern = r"vmess://([^#]+)$"
    match = re.match(pattern, uri)
    if not match:
        return None
    b64_part_raw = match.group(1)
    b64_part_decode = ctx.processors_map["decode_b64_simple"](b64_part_raw)
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
    address = ctx.processors_map["to_lower"](address_raw)
    port = ctx.processors_map["to_int"](port_raw)
    uuid = ctx.processors_map["id_to_uuid"](id_raw)
    params = ctx.processors_map["extract_params_vmess"](obj_data)
    params_protocol = ctx.processors_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "vmess",
        "address": address,
        "port": port,
        "id": uuid,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    remarks = protocol_dict["type"][:2]
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
        "remarks": remarks,
    }
    return obj


def parse_vmess_uri_format(uri, protocol_values, ctx):
    pattern = r"vmess://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    id_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = ctx.processors_map["parse_params"](query_raw)
    address = ctx.processors_map["to_lower"](address_raw)
    port = ctx.processors_map["to_int"](port_raw)
    uuid = ctx.processors_map["id_to_uuid"](id_raw)
    params_protocol = ctx.processors_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "vmess",
        "address": address,
        "port": port,
        "id": uuid,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    remarks = protocol_dict["type"][:2]
    obj = {
        "protocol": protocol_dict,
        "security": {},
        "transport": {},
        "params": params,
        "remarks": remarks,
    }
    return obj


def parse_hysteria2_uri(uri, protocol_values, ctx):
    pattern = r"hysteria2://([^@]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None
    password_raw = match.group(1)
    address_raw = match.group(2)
    port_raw = match.group(3)
    query_raw = match.group(4) or ""
    params = ctx.processors_map["parse_params"](query_raw)
    address = ctx.processors_map["to_lower"](address_raw)
    port = ctx.processors_map["to_int"](port_raw)
    params_protocol = ctx.processors_map["extract_params"](params, protocol_values)
    protocol_dict = {
        "type": "hysteria2",
        "address": address,
        "port": port,
        "password": password_raw,
    }
    if params_protocol is not None:
        protocol_dict.update(params_protocol)
    remarks = (
        protocol_dict["type"][:2]
        + ("-tl" if "sni" in protocol_dict else "-no")
        + ("-ud" if "obfs" in protocol_dict else "-qu")
    )
    obj = {
        "protocol": protocol_dict,
        "params": params,
        "remarks": remarks,
    }
    return obj


def compute_hash(obj, ctx):
    hash_input = {k: v for k, v in obj.items()}
    hash_input = ctx.processors_map["case_insensitive_hash"](hash_input)
    hash_string = json.dumps(hash_input, sort_keys=True, default=str)
    hash_obj = hashlib.sha256(hash_string.encode("utf-8"))
    return hash_obj.hexdigest()


def process_security(proxy_object, ctx):
    securities_object = ctx.configs_map["PROXIES"]["SECURITIES"]
    if not proxy_object:
        return None
    if proxy_object.get("security") != {}:
        return proxy_object
    params = proxy_object.get("params", {})
    security_raw = str(params.get("security", "")).strip().lower()
    if not security_raw or security_raw not in securities_object:
        security_type = "none"
    else:
        security_type = security_raw
    security_obj = {"type": security_type}
    if security_type != "none":
        security_values = securities_object[security_type]
        security_params = ctx.processors_map["extract_params"](params, security_values)
        if security_params is None:
            return None
        security_obj = {**security_obj, **security_params}
    proxy_object["security"] = security_obj
    return proxy_object


def process_transport(proxy_object, ctx):
    transports_object = ctx.configs_map["PROXIES"]["TRANSPORTS"]
    if not proxy_object:
        return None
    if proxy_object.get("transport") != {}:
        return proxy_object
    params = proxy_object.get("params", {})
    transport_raw = str(params.get("type", "")).strip().lower()
    if not transport_raw or transport_raw not in transports_object:
        transport_type = "raw"
    else:
        transport_type = transport_raw
    transport_obj = {"type": transport_type}
    transport_values = transports_object[transport_type]
    tarnsport_params = ctx.processors_map["extract_params"](params, transport_values)
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
        transport_obj["path"] = ctx.processors_map["path_start_with_slash"](
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
