import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch import fetch_content_to_file
from transform import transform_uris
from utils.config import configs_map
from utils.processors import processors_map
from utils.helpers import helpers_map


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [fetch|transform]")
        sys.exit(1)
    command = sys.argv[1].lower()
    match command:
        case "fetch":
            fetch_content_to_file(configs_map, processors_map)
        case "transform":
            transform_uris(configs_map, processors_map, helpers_map)
        case _:
            sys.exit(1)


if __name__ == "__main__":
    main()
