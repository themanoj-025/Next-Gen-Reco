"""Parquet-first table loading helpers.

The datasets under ``data/`` historically shipped as CSV (``tags.csv`` alone
is ~72MB / 2M rows and dominated app startup).  They are now migrated to
Parquet, which is columnar and memory-maps on read.  These helpers keep the
CSV path working as a fallback (tests and legacy checkouts) while preferring
a ``.parquet`` sibling whenever it exists.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

#: Rows per chunk when falling back to a large CSV.  Keeps peak memory bounded
#: while still producing one concatenated DataFrame (callers see a normal frame).
CSV_CHUNKSIZE = 500_000


def parquet_preferred(path: str | Path) -> Path:
    """Return the ``.parquet`` sibling for a ``.csv`` path if it exists.

    Non-CSV paths are returned unchanged, as are CSV paths with no Parquet
    sibling — so callers can pass either format transparently.
    """
    p = Path(path)
    if p.suffix.lower() == ".csv":
        sibling = p.with_suffix(".parquet")
        if sibling.exists():
            return sibling
    return p


def read_table(
    path: str | Path,
    *,
    dtype: dict | None = None,
    low_memory: bool | None = None,
    chunksize: int | None = None,
) -> pd.DataFrame:
    """Read a table from Parquet when available, else CSV.

    Parameters mirror the ``pd.read_csv`` keywords used at call sites so the
    CSV-only options are harmless no-ops on the Parquet path.

    - Parquet: single memory-mapped read (fast path).
    - CSV without ``chunksize``: plain ``pd.read_csv``.
    - CSV with ``chunksize``: chunked read concatenated into one DataFrame so
      a 2M-row file never materializes as a single parser buffer.
    """
    src = parquet_preferred(path)
    if src.suffix.lower() == ".parquet":
        return pd.read_parquet(src)

    if chunksize is not None:
        chunks = pd.read_csv(src, chunksize=chunksize, dtype=dtype, low_memory=low_memory)
        return pd.concat(chunks, ignore_index=True)

    return pd.read_csv(src, dtype=dtype, low_memory=low_memory)
