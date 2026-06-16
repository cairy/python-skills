# /// script
# dependencies = [
#   "sqlalchemy>=2.0",
#   "pyodbc>=4.0; platform_system!='Linux'",
# ]
# requires-python = ">=3.10"
# ///

"""db-tools CLI placeholder."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Database connection and query tool")
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
