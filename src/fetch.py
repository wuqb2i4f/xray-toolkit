import urllib.request
import urllib.error
import base64
from config.config import LINKS, URIS_RAW_PATH, URIS_RAW_REJECTED_PATH, PROXIES
from utils.processors import processors_map
import os


def fetch_content_to_file() -> None:
    """
    Orchestrate extraction: Fetch from URLs, parse URIs, write to single URI file and rejected file.
    Uses PROXIES config for routing/normalization.
    """
    rejected_lines = set()
    total_processed = 0
    all_uris = set()

    # Create full prefixes dynamically
    full_prefixes = [p + "://" for p in PROXIES["PROTOCOLS"].keys()]

    for url in LINKS:
        try:
            content = fetch_url_content(url)
            protocol_uris_temp, rejected_temp = parse_content_to_uris(
                content, full_prefixes
            )

            # Merge temp sets into main all_uris
            for uris in protocol_uris_temp.values():
                all_uris.update(uris)
            rejected_lines.update(rejected_temp)
            # Rough line count (non-empty after strip)
            total_processed += sum(
                1 for line in content.strip().split("\n") if line.strip()
            )

        except (urllib.error.URLError, ValueError) as e:
            print(f"Error fetching {url}: {e}")
            continue

    # Write files (now cumulative with dedup and sort)
    write_rejected_file(rejected_lines)
    write_uris_file(all_uris)

    print(f"Processed {total_processed} lines from {len(LINKS)} URLs.")
    return None


def fetch_url_content(url):
    """Fetch and decode (Base64 fallback) content from one URL."""
    with urllib.request.urlopen(url) as response:
        raw_content = response.read().decode("utf-8")

    try:
        decoded_bytes = base64.b64decode(raw_content)
        return decoded_bytes.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return raw_content


def parse_content_to_uris(content, full_prefixes):
    """Parse lines, filter/normalize URIs, return protocol sets and rejected."""
    protocol_uris_temp = {proto: set() for proto in PROXIES["PROTOCOLS"].keys()}
    rejected_temp = set()

    lines = content.strip().split("\n")
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        if stripped_line.startswith(tuple(full_prefixes)):
            # Detect and normalize
            for prefix in full_prefixes:
                if stripped_line.startswith(prefix):
                    base_proto = prefix.rstrip("://")
                    proto_config = PROXIES["PROTOCOLS"].get(base_proto, {})

                    # Check if processors are specified in config's "uri"
                    if "uri" in proto_config and "processors" in proto_config["uri"]:
                        processors_list = proto_config["uri"]["processors"]
                        normalized_uri = stripped_line
                        # Apply each processor in sequence
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
    """Read existing lines from file into a set for deduplication."""
    existing_lines = set()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    existing_lines.add(stripped)
    return existing_lines


def write_uris_file(new_uris):
    """Append new URIs to existing single file, deduplicate, sort, and rewrite."""
    if new_uris:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(URIS_RAW_PATH), exist_ok=True)

        # Read existing
        existing_uris = read_existing_lines(URIS_RAW_PATH)

        # Decode new URIs
        decoded_new_uris = {
            processors_map["decode_url_encode"](uri) for uri in new_uris
        }

        # Merge and dedup
        all_uris = existing_uris.union(decoded_new_uris)

        # Sort and write
        with open(URIS_RAW_PATH, "w", encoding="utf-8") as f:
            for uri in sorted(all_uris):
                f.write(uri + "\n")

        added_count = len(new_uris) - len(new_uris.intersection(existing_uris))
        print(
            f"Appended {added_count} new unique URIs (total: {len(all_uris)}) to {URIS_RAW_PATH}."
        )


def write_rejected_file(new_rejected_lines):
    """Append new rejected lines to existing file, deduplicate, sort, and rewrite."""
    # Read existing
    existing_rejected = read_existing_lines(URIS_RAW_REJECTED_PATH)

    # Merge and dedup
    all_rejected = existing_rejected.union(new_rejected_lines)

    # Sort and write
    with open(URIS_RAW_REJECTED_PATH, "w", encoding="utf-8") as f:
        for line in sorted(all_rejected):
            f.write(line + "\n")

    added_count = len(new_rejected_lines) - len(
        new_rejected_lines.intersection(existing_rejected)
    )
    print(
        f"Appended {added_count} new unique rejected lines (total: {len(all_rejected)}) to {URIS_RAW_REJECTED_PATH}."
    )


# For testing
if __name__ == "__main__":
    fetch_content_to_file()
