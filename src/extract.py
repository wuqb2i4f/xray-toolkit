import urllib.request
import urllib.error
import base64
from typing import Dict, Set, Tuple, List
from config.config import LINKS, REJECTED_URIS_PATH, PROXIES
from utils.processors import processors_map
import os


def extract_content_to_file() -> None:
    """
    Orchestrate extraction: Fetch from URLs, parse URIs, write to protocol/rejected files.
    Uses PROXIES config for routing/normalization.
    """
    rejected_lines: Set[str] = set()
    total_processed: int = 0

    # Create full prefixes dynamically
    full_prefixes: List[str] = [p + "://" for p in PROXIES["PROTOCOLS"].keys()]

    # Per-protocol URIs for specific files
    protocol_uris: Dict[str, Set[str]] = {
        proto: set() for proto in PROXIES["PROTOCOLS"].keys()
    }

    for url in LINKS:
        try:
            content = fetch_url_content(url)
            protocol_uris_temp, rejected_temp = parse_content_to_uris(
                content, full_prefixes
            )

            # Merge temp sets into main (for aggregation across URLs)
            for proto, uris in protocol_uris_temp.items():
                protocol_uris[proto].update(uris)
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
    write_protocol_files(protocol_uris)

    print(f"Processed {total_processed} lines from {len(LINKS)} URLs.")
    return None


def fetch_url_content(url: str) -> str:
    """Fetch and decode (Base64 fallback) content from one URL."""
    with urllib.request.urlopen(url) as response:
        raw_content = response.read().decode("utf-8")

    try:
        decoded_bytes = base64.b64decode(raw_content)
        return decoded_bytes.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return raw_content


def parse_content_to_uris(
    content: str, full_prefixes: List[str]
) -> Tuple[Dict[str, Set[str]], Set[str]]:
    """Parse lines, filter/normalize URIs, return protocol sets and rejected."""
    protocol_uris_temp: Dict[str, Set[str]] = {
        proto: set() for proto in PROXIES["PROTOCOLS"].keys()
    }
    rejected_temp: Set[str] = set()

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

                    # Check if normalize is specified in config's "uri"
                    if "uri" in proto_config and "normalize" in proto_config["uri"]:
                        norm_rule = proto_config["uri"]["normalize"]
                        normalized_uri, output_proto = normalize_uri(
                            stripped_line, prefix, norm_rule
                        )
                    else:
                        normalized_uri, output_proto = (stripped_line, base_proto)

                    if output_proto in protocol_uris_temp:
                        protocol_uris_temp[output_proto].add(normalized_uri)
                    break
        else:
            rejected_temp.add(stripped_line)

    return protocol_uris_temp, rejected_temp


def normalize_uri(uri: str, prefix: str, norm_rule: str) -> Tuple[str, str]:
    """Apply normalization based on rule string; returns (normalized_uri, target_proto).
    Uses imported normalizers map for dynamic lookup.
    """
    base_proto = prefix.rstrip("://")
    if norm_rule in processors_map:
        uri = processors_map[norm_rule](uri)
        return uri, base_proto
    else:
        print(
            f"Unknown normalize rule '{norm_rule}' - using original URI and base proto"
        )
        return uri, base_proto


def read_existing_lines(file_path: str) -> Set[str]:
    """Read existing lines from file into a set for deduplication."""
    existing_lines = set()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    existing_lines.add(stripped)
    return existing_lines


def write_protocol_files(protocol_uris: Dict[str, Set[str]]) -> None:
    """Append new URIs to existing files, deduplicate, sort, and rewrite."""
    for proto, new_uris in protocol_uris.items():
        if new_uris:
            proto_config = PROXIES["PROTOCOLS"][proto]
            output_path = proto_config["uri"]["raw_output"]

            # Read existing
            existing_uris = read_existing_lines(output_path)

            # Merge and dedup
            all_uris = existing_uris.union(new_uris)

            # Sort and write
            with open(output_path, "w", encoding="utf-8") as f:
                for uri in sorted(all_uris):
                    f.write(uri + "\n")

            added_count = len(new_uris) - len(new_uris.intersection(existing_uris))
            print(
                f"Appended {added_count} new unique {proto} URIs (total: {len(all_uris)}) to {output_path}."
            )


def write_rejected_file(new_rejected_lines: Set[str]) -> None:
    """Append new rejected lines to existing file, deduplicate, sort, and rewrite."""
    # Read existing
    existing_rejected = read_existing_lines(REJECTED_URIS_PATH)

    # Merge and dedup
    all_rejected = existing_rejected.union(new_rejected_lines)

    # Sort and write
    with open(REJECTED_URIS_PATH, "w", encoding="utf-8") as f:
        for line in sorted(all_rejected):
            f.write(line + "\n")

    added_count = len(new_rejected_lines) - len(
        new_rejected_lines.intersection(existing_rejected)
    )
    print(
        f"Appended {added_count} new unique rejected lines (total: {len(all_rejected)}) to {REJECTED_URIS_PATH}."
    )


# For testing
if __name__ == "__main__":
    extract_content_to_file()
