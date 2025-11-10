import urllib.request
import urllib.error
import base64
from typing import Dict, Set, Tuple, List
from config.config import LINKS, REJECTED_URIS_PATH, PROXIES
from utils.processors import processors


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

    # Write files
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
    if norm_rule in processors:
        return processors[norm_rule](uri, prefix)
    else:
        print(
            f"Unknown normalize rule '{norm_rule}' - using original URI and base proto"
        )
        base_proto = prefix.rstrip("://")
        return uri, base_proto


def write_protocol_files(protocol_uris: Dict[str, Set[str]]) -> None:
    """Write each protocol's URIs to its output file."""
    for proto, uris in protocol_uris.items():
        if uris:
            proto_config = PROXIES["PROTOCOLS"][proto]
            output_path = proto_config["uri"]["raw_output"]
            with open(output_path, "w", encoding="utf-8") as f:
                for uri in sorted(uris):
                    f.write(uri + "\n")
            print(f"Saved {len(uris)} unique {proto} URIs to {output_path}.")


def write_rejected_file(rejected_lines: Set[str]) -> None:
    """Write rejected lines to file."""
    with open(REJECTED_URIS_PATH, "w", encoding="utf-8") as f:
        for line in sorted(rejected_lines):
            f.write(line + "\n")
    print(f"Saved {len(rejected_lines)} unique rejected lines to {REJECTED_URIS_PATH}.")


# For testing
if __name__ == "__main__":
    extract_content_to_file()
