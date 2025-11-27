import base64
import os
import tempfile
import urllib.error
import urllib.request


def fetch_uris(configs_map, processors_map, database_map):
    links = configs_map["LINKS"]
    protocols_object = configs_map["PROXIES"]["PROTOCOLS"]
    db_path = configs_map["DB_PATH"]
    schemas = configs_map["TABLE_SCHEMAS"]
    database_map["ensure_table"](db_path, "uris_raw", schemas["uris_raw"])
    database_map["ensure_table"](db_path, "uris_rejected", schemas["uris_rejected"])
    total_processed = 0
    all_uris = set()
    rejected_lines = set()
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
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
    added_valid = save_uris_to_db(all_uris, db_path, database_map, processors_map)
    added_rejected = save_rejected_to_db(rejected_lines, db_path, database_map)
    total_valid = database_map["count_records"](db_path, "uris_raw")
    total_rejected = database_map["count_records"](db_path, "uris_rejected")
    print(f"Fetch complete → {added_valid} new valid, {added_rejected} rejected")
    print(f"Total in DB → valid: {total_valid}, rejected: {total_rejected}")
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


def save_uris_to_db(uris_set, db_path, database_map, processors_map):
    if not uris_set:
        return 0
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
        for uri in sorted(uris_set):
            decoded = processors_map["decode_url_encode"](uri)
            f.write(decoded + "\n")
        temp_path = f.name
    try:
        records = uri_generator(temp_path)
        added = database_map["bulk_upsert"](
            db_path=db_path,
            table_name="uris_raw",
            records=records,
            key_columns="uri",
        )
        return added
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def save_rejected_to_db(rejected_lines_set, db_path, database_map):
    if not rejected_lines_set:
        return 0
    records = [(line.strip(),) for line in rejected_lines_set if line.strip()]
    if not records:
        return 0
    with database_map["get_db_connection"](db_path) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO uris_rejected (line) VALUES (?)",
            records,
        )
        conn.commit()
    return len(records)


def uri_generator(file_path):
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            uri = line.strip()
            if uri:
                yield {"uri": uri}
