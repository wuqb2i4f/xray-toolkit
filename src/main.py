import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from context import AppContext
from fetch import fetch_uris
from transform import transform_uris


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main [fetch|transform|all]")
        sys.exit(1)
    ctx = AppContext()
    command = sys.argv[1].lower()
    if command in ["fetch", "all"]:
        print("Fetching new proxies...")
        fetch_uris(ctx)
    if command in ["transform", "all"]:
        print("Transforming and deduplicating...")
        transform_uris(ctx)
    print("Optimizing database size...")
    ctx.database_map["optimize_database"](db_path=ctx.configs_map["DB_PATH"])


if __name__ == "__main__":
    main()
