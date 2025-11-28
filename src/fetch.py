import base64
import os
import tempfile
import urllib.error
import urllib.request


def fetch_uris(ctx):
    links = ctx.configs_map["LINKS"]
    total_processed = 0
    all_uris = set()
    rejected_lines = set()
    for url in links:
        try:
            content = fetch_url_content(url)
            protocol_uris_temp, rejected_temp = parse_content_to_uris(content, ctx)
            for uris in protocol_uris_temp.values():
                all_uris.update(uris)
            rejected_lines.update(rejected_temp)
            total_processed += sum(
                1 for line in content.strip().split("\n") if line.strip()
            )
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
    db_path = ctx.configs_map["DB_PATH"]
    schemas = ctx.configs_map["TABLE_SCHEMAS"]
    ctx.database_map["ensure_table"](
        db_path=db_path, table_name="uris_raw", columns=schemas["uris_raw"]
    )
    ctx.database_map["ensure_table"](
        db_path=db_path, table_name="uris_rejected", columns=schemas["uris_rejected"]
    )
    added_valid = save_uris_to_db(all_uris, db_path, ctx)
    added_rejected = save_rejected_to_db(rejected_lines, db_path, ctx)
    total_valid = ctx.database_map["count_records"](
        db_path=db_path, table_name="uris_raw"
    )
    total_rejected = ctx.database_map["count_records"](
        db_path=db_path, table_name="uris_rejected"
    )
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


def parse_content_to_uris(content, ctx):
    protocols_object = ctx.configs_map["PROXIES"]["PROTOCOLS"]
    valid_uris = {proto: set() for proto in protocols_object}
    rejected = set()
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        for proto in protocols_object:
            prefix = f"{proto}://"
            if not line.startswith(prefix):
                continue
            rules = protocols_object[proto].get("uri", {}).get("processors", [])
            normalized = line
            for rule in rules:
                if rule not in ctx.processors_map:
                    print(f"Unknown processor rule '{rule}' - skipping for URI: {line}")
                    continue
                normalized = ctx.processors_map[rule](normalized)
            valid_uris[proto].add(normalized)
            break
        else:
            rejected.add(line)
    return valid_uris, rejected


def save_uris_to_db(uris_set, db_path, ctx):
    if not uris_set:
        return 0
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
        for uri in sorted(uris_set):
            decoded = ctx.processors_map["decode_url_encode"](uri)
            f.write(decoded + "\n")
        temp_path = f.name
    try:
        records = ctx.processors_map["uri_generator"](temp_path)
        added = ctx.database_map["bulk_upsert"](
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


def save_rejected_to_db(rejected_lines_set, db_path, ctx):
    if not rejected_lines_set:
        return 0
    records = [(line.strip(),) for line in rejected_lines_set if line.strip()]
    if not records:
        return 0
    with ctx.database_map["get_db_connection"](db_path) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO uris_rejected (line) VALUES (?)",
            records,
        )
        conn.commit()
    return len(records)
