import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context import AppContext
from fetch import fetch_uris
from transform import transform_uris


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [fetch|transform]")
        sys.exit(1)
    ctx = AppContext()
    command = sys.argv[1].lower()
    match command:
        case "fetch":
            fetch_uris(ctx)
        case "transform":
            transform_uris(ctx)
        case _:
            sys.exit(1)


if __name__ == "__main__":
    main()
