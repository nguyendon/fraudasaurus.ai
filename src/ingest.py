"""Data ingestion module for Fraudasaurus.ai.

Loads raw datasets from multiple formats, profiles them,
and returns clean DataFrames ready for downstream processing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls", ".parquet"}


def load_file(path: str | Path) -> pd.DataFrame:
    """Load a single file into a DataFrame, auto-detecting format by extension.

    Supported formats: CSV, JSON, Excel (.xlsx/.xls), Parquet.

    Args:
        path: Path to the data file.

    Returns:
        A pandas DataFrame with the file contents.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    loaders = {
        ".csv": pd.read_csv,
        ".json": pd.read_json,
        ".xlsx": pd.read_excel,
        ".xls": pd.read_excel,
        ".parquet": pd.read_parquet,
    }

    loader = loaders.get(ext)
    if loader is None:
        raise ValueError(
            f"Unsupported file format '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    return loader(path)


def load_all_datasets(data_dir: str | Path = "data/raw") -> dict[str, pd.DataFrame]:
    """Scan a directory and load every supported file into a dict.

    Args:
        data_dir: Directory to scan for data files.

    Returns:
        Dict mapping filename to its DataFrame.
    """
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        logger.warning("Directory does not exist: %s", data_dir)
        return {}

    files = [
        f for f in sorted(data_dir.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        logger.info("No supported files found in %s", data_dir)
        return {}

    datasets: dict[str, pd.DataFrame] = {}
    for filepath in tqdm(files, desc="Loading datasets"):
        try:
            datasets[filepath.name] = load_file(filepath)
            logger.info("Loaded %s (%s rows)", filepath.name, len(datasets[filepath.name]))
        except Exception:
            logger.warning("Skipping %s — failed to load", filepath.name, exc_info=True)

    return datasets


def profile_dataset(df: pd.DataFrame, name: str = "") -> dict[str, Any]:
    """Print and return a summary profile of a DataFrame.

    Includes shape, dtypes, null counts, basic statistics, and a sample.

    Args:
        df: The DataFrame to profile.
        name: Optional label for display.

    Returns:
        Dict with keys: shape, dtypes, null_counts, stats, sample.
    """
    header = f"=== Profile: {name} ===" if name else "=== Dataset Profile ==="
    print(header)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")

    print("\nColumn types:")
    for col, dtype in df.dtypes.items():
        print(f"  {col}: {dtype}")

    null_counts = df.isnull().sum()
    if null_counts.any():
        print("\nNull counts:")
        for col, count in null_counts[null_counts > 0].items():
            print(f"  {col}: {count}")
    else:
        print("\nNo null values.")

    print("\nBasic statistics:")
    print(df.describe(include="all").to_string())

    sample = df.head(5)
    print("\nSample (first 5 rows):")
    print(sample.to_string())

    return {
        "shape": df.shape,
        "dtypes": df.dtypes.to_dict(),
        "null_counts": null_counts.to_dict(),
        "stats": df.describe(include="all"),
        "sample": sample,
    }
