"""Compact, reader-friendly Parquet files for per-instance signals and spectra."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .paths import MAX_FILE_MB


def trim_mantissa(x: np.ndarray, keep_bits: int = 12) -> np.ndarray:
    """Round float32 values to `keep_bits` mantissa bits (relative error <= 2**-(keep_bits+1)).

    The dropped low bits become zero, which byte_stream_split + zstd compress to almost
    nothing, so the files shrink to roughly float16 size while staying plain float32
    (read as is by pandas/pyarrow and DuckDB).
    """
    drop = 23 - keep_bits
    bits = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    rounded = (bits + np.uint32(1 << (drop - 1))) & np.uint32((0xFFFFFFFF << drop) & 0xFFFFFFFF)
    return rounded.view(np.float32)


def write_compact(df: pd.DataFrame, path: Path, float_cols: list[str] | None = None,
                  row_group_size: int = 50_000) -> float:
    """zstd-19 Parquet with BYTE_STREAM_SPLIT on the float32 columns; returns the size in MB."""
    if float_cols is None:
        float_cols = [c for c in df.columns if df[c].dtype == np.float32]
    path.parent.mkdir(parents=True, exist_ok=True)
    # dictionary encoding would block byte_stream_split and triples the size of float columns
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), path, compression="zstd",
                   compression_level=19, use_dictionary=False, use_byte_stream_split=float_cols,
                   row_group_size=row_group_size)
    mb = path.stat().st_size / 2**20
    if mb > MAX_FILE_MB:
        raise RuntimeError(f"{path.name} is {mb:.1f} MB > {MAX_FILE_MB} MB; split it")
    return mb
