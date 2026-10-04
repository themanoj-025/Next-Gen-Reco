#!/usr/bin/env python3
"""Migrate the tracked MovieLens CSVs to Parquet.

Reads each source CSV with the dtype-preserving options the loaders use and
writes a ``.parquet`` sibling next to it.  Idempotent — pass ``--force`` to
rewrite existing Parquet files.

Usage:
    python scripts/migrate_to_parquet.py [--force]

After migrating:
    * the CSVs are untracked from git (Parquet is tracked instead)
    * loaders prefer Parquet automatically (see app/data/tables.py)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# (csv path, read kwargs) — kwargs mirror the production loaders' CSV path.
SOURCES: list[tuple[Path, dict]] = [
    (PROJECT_ROOT / "data" / "movies.csv", {}),
    (
        PROJECT_ROOT / "data" / "tags.csv",
        {"dtype": {"userId": "int32", "movieId": "int32", "tag": "object"}},
    ),
    (PROJECT_ROOT / "data" / "ND" / "movies.csv", {"low_memory": False}),
]


def migrate(force: bool = False) -> int:
    failures = 0
    for csv_path, kwargs in SOURCES:
        if not csv_path.exists():
            print(f"  [skip missing] {csv_path.relative_to(PROJECT_ROOT)}")
            continue
        out_path = csv_path.with_suffix(".parquet")
        if out_path.exists() and not force:
            print(f"  [exists] {out_path.relative_to(PROJECT_ROOT)}")
            continue
        try:
            df = pd.read_csv(csv_path, **kwargs)
            df.to_parquet(out_path, index=False)
        except (OSError, ValueError) as e:
            print(f"  [FAIL] {csv_path.name}: {e}")
            failures += 1
            continue

        # Round-trip sanity: row count must survive the conversion.
        check = pd.read_parquet(out_path)
        ok = len(check) == len(df)
        if not ok:
            failures += 1
        status = "ok" if ok else "ROW COUNT MISMATCH"
        print(
            f"  {status} {csv_path.name} -> {out_path.name} "
            f"({len(df):,} rows, {csv_path.stat().st_size // 1_048_576}MB -> "
            f"{out_path.stat().st_size // 1_048_576}MB)"
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rewrite existing Parquet files")
    args = parser.parse_args()
    print("CSV -> Parquet migration:")
    return 1 if migrate(force=args.force) else 0


if __name__ == "__main__":
    sys.exit(main())
