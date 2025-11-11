import json
import re
from typing import Dict, List, Any
from config.config import PROXIES
from utils.helpers import validate_object
from utils.processors import processors


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
    """Validate and parse URIs using fields config; return list of dicts."""
    processed = []
    for uri in uris:
        obj = parse_and_validate_uri(uri, proto, fields_config)
        if obj:
            processed.append(obj)
    print(f"Processed {len(processed)} valid {proto} URIs from {len(uris)} raw.")
    return processed


def parse_and_validate_uri(
    uri: str, proto: str, fields_config: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Parse URI to dict based on protocol, validate using fields config."""
    if proto == "ss":
        return parse_ss_uri(uri, fields_config)
    # Placeholder for other protocols
    else:
        print(f"No parser for {proto} yet - skipping.")
        return None


def parse_ss_uri(uri: str, fields_config: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse SS URI using small helpers, then validate full object."""
    components = extract_ss_components(uri)
    if not components:
        return None

    obj = build_ss_object(components)
    if not validate_object(obj, fields_config):
        return None

    return obj


def extract_ss_components(uri: str) -> Dict[str, str] | None:
    """Extract base64, address, port, params, remarks from SS URI regex match."""
    pattern = r"ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)(?:\?([^#]*))?(?:#(.*))?$"
    match = re.match(pattern, uri)
    if not match:
        return None

    return {
        "b64_part": match.group(1),
        "address": match.group(2),
        "port_str": match.group(3),
        "params_str": match.group(4) or "",
        "remarks": match.group(5) or "",
    }


def build_ss_object(components: Dict[str, str]) -> Dict[str, Any] | None:
    """Build SS dict from components."""
    port_str = components["port_str"]
    try:
        port = int(port_str)
    except ValueError:
        return None

    decode_result = processors["decode_b64_simple"](components["b64_part"])
    if not decode_result:
        return None
    method, password = decode_result.split(":", 1)

    params_str = components["params_str"]
    params = {}
    if params_str:
        for pair in params_str.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v

    remarks = processors["decode_remarks"](components["remarks"])

    return {
        "address": components["address"],
        "port": port,
        "password": password,
        "method": method,
        "keys": params,
        "remarks": remarks,
    }


def write_json_file(objects: List[Dict[str, Any]], file_path: str, proto: str) -> None:
    """Write list of dicts as JSON array to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON with {len(objects)} processed {proto} URIs to {file_path}.")


# For testing
if __name__ == "__main__":
    transform_uris()
