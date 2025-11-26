import base64
import os
import urllib.error
import urllib.request


def fetch_uris(configs_map, processors_map):
    links = configs_map["LINKS"]
    protocols_object = configs_map["PROXIES"]["PROTOCOLS"]
    uris_raw_path = configs_map["URIS_RAW_PATH"]
    uris_raw_rejected_path = configs_map["URIS_RAW_REJECTED_PATH"]
    rejected_lines = set()
    total_processed = 0
    all_uris = set()
    for url in links:
        try:
            content = fetch_url_content(url)
            protocol_uris_temp, rejected_temp = parse_content_to_uris(
                content, protocols_object, processors_map
            )
            for uris in protocol_uris_temp.values():
                all_uris.update(uris)
            rejected_lines.update(rejected_temp)
            total_processed += sum(
                1 for line in content.strip().split("\n") if line.strip()
            )
        except (urllib.error.URLError, ValueError) as e:
            print(f"Error fetching {url}: {e}")
            continue
    write_rejected_file(rejected_lines, uris_raw_rejected_path)
    write_uris_file(all_uris, uris_raw_path, processors_map)
    print(f"Processed {total_processed} lines from {len(links)} URLs.")
    return None


def fetch_url_content(url):
    with urllib.request.urlopen(url) as response:
        raw_content = response.read().decode("utf-8")
    try:
        decoded_bytes = base64.b64decode(raw_content)
        return decoded_bytes.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return raw_content


def parse_content_to_uris(content, protocols_object, processors_map):
    full_prefixes = [p + "://" for p in protocols_object.keys()]
    protocol_uris_temp = {proto: set() for proto in protocols_object.keys()}
    rejected_temp = set()
    lines = content.strip().split("\n")
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith(tuple(full_prefixes)):
            for prefix in full_prefixes:
                if stripped_line.startswith(prefix):
                    base_proto = prefix.rstrip("://")
                    proto_config = protocols_object.get(base_proto, {})
                    if "uri" in proto_config and "processors" in proto_config["uri"]:
                        processors_list = proto_config["uri"]["processors"]
                        normalized_uri = stripped_line
                        for norm_rule in processors_list:
                            if norm_rule in processors_map:
                                normalized_uri = processors_map[norm_rule](
                                    normalized_uri
                                )
                            else:
                                print(
                                    f"Unknown processor rule '{norm_rule}' - skipping for URI: {normalized_uri}"
                                )
                        output_proto = base_proto
                    else:
                        normalized_uri, output_proto = (stripped_line, base_proto)
                    if output_proto in protocol_uris_temp:
                        protocol_uris_temp[output_proto].add(normalized_uri)
                    break
        else:
            rejected_temp.add(stripped_line)
    return protocol_uris_temp, rejected_temp


def read_existing_lines(file_path):
    existing_lines = set()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    existing_lines.add(stripped)
    return existing_lines


def write_uris_file(new_uris, uris_raw_path, processors_map):
    if new_uris:
        os.makedirs(os.path.dirname(uris_raw_path), exist_ok=True)
        existing_uris = read_existing_lines(uris_raw_path)
        decoded_new_uris = {
            processors_map["decode_url_encode"](uri) for uri in new_uris
        }
        all_uris = existing_uris.union(decoded_new_uris)
        with open(uris_raw_path, "w", encoding="utf-8") as f:
            for uri in sorted(all_uris):
                f.write(uri + "\n")
        added_count = len(new_uris) - len(new_uris.intersection(existing_uris))
        print(
            f"Appended {added_count} new unique URIs (total: {len(all_uris)}) to {uris_raw_path}."
        )


def write_rejected_file(new_rejected_lines, uris_raw_rejected_path):
    existing_rejected = read_existing_lines(uris_raw_rejected_path)
    all_rejected = existing_rejected.union(new_rejected_lines)
    with open(uris_raw_rejected_path, "w", encoding="utf-8") as f:
        for line in sorted(all_rejected):
            f.write(line + "\n")
    added_count = len(new_rejected_lines) - len(
        new_rejected_lines.intersection(existing_rejected)
    )
    print(
        f"Appended {added_count} new unique rejected lines (total: {len(all_rejected)}) to {uris_raw_rejected_path}."
    )
