"""Data cleaning module for Fraudasaurus.ai.

Provides composable cleaning steps and a single pipeline
function that runs them all in sequence.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and replace spaces/special chars with underscores.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with cleaned column names.
    """
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.strip("_")
    )
    return df


def parse_dates(
    df: pd.DataFrame,
    date_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Parse date columns to datetime.

    If *date_cols* is None, auto-detect columns whose name contains
    'date', 'time', 'timestamp', or 'dt'.

    Args:
        df: Input DataFrame.
        date_cols: Explicit list of columns to parse, or None to auto-detect.

    Returns:
        DataFrame with date columns converted to datetime.
    """
    df = df.copy()
    if date_cols is None:
        pattern = re.compile(r"date|time|timestamp|_dt$|^dt_", re.IGNORECASE)
        date_cols = [c for c in df.columns if pattern.search(c)]

    for col in date_cols:
        if col not in df.columns:
            logger.warning("Date column '%s' not found — skipping", col)
            continue
        try:
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            logger.info("Parsed '%s' as datetime", col)
        except Exception:
            logger.warning("Could not parse '%s' as datetime", col, exc_info=True)

    return df


def standardize_amounts(
    df: pd.DataFrame,
    amount_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Strip currency symbols and convert amount columns to float.

    If *amount_cols* is None, auto-detect columns whose name contains
    'amount', 'price', 'cost', 'total', 'fee', or 'balance'.

    Args:
        df: Input DataFrame.
        amount_cols: Explicit list of columns to clean, or None to auto-detect.

    Returns:
        DataFrame with amount columns as float64.
    """
    df = df.copy()
    if amount_cols is None:
        pattern = re.compile(
            r"amount|price|cost|total|fee|balance|revenue|payment", re.IGNORECASE
        )
        amount_cols = [c for c in df.columns if pattern.search(c)]

    for col in amount_cols:
        if col not in df.columns:
            logger.warning("Amount column '%s' not found — skipping", col)
            continue
        if df[col].dtype == "object":
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[^\d.\-]", "", regex=True)
            )
        df[col] = pd.to_numeric(df[col], errors="coerce")
        logger.info("Standardized '%s' as float", col)

    return df


def deduplicate(
    df: pd.DataFrame,
    subset: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Remove duplicate rows.

    Args:
        df: Input DataFrame.
        subset: Columns to consider for identifying duplicates.
                If None, all columns are used.

    Returns:
        DataFrame with duplicates removed.
    """
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    removed = before - len(df)
    if removed:
        logger.info("Removed %d duplicate rows", removed)
    else:
        logger.info("No duplicate rows found")
    return df


def clean_pipeline(
    df: pd.DataFrame,
    date_cols: Sequence[str] | None = None,
    amount_cols: Sequence[str] | None = None,
    dedup_subset: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Run the full cleaning pipeline in sequence.

    Steps:
        1. Normalize column names
        2. Parse date columns
        3. Standardize amount columns
        4. Remove duplicates

    Args:
        df: Raw input DataFrame.
        date_cols: Passed to parse_dates (None = auto-detect).
        amount_cols: Passed to standardize_amounts (None = auto-detect).
        dedup_subset: Passed to deduplicate (None = all columns).

    Returns:
        Cleaned DataFrame.
    """
    logger.info("Starting cleaning pipeline (%d rows, %d cols)", *df.shape)

    df = normalize_columns(df)
    df = parse_dates(df, date_cols=date_cols)
    df = standardize_amounts(df, amount_cols=amount_cols)
    df = deduplicate(df, subset=dedup_subset)

    logger.info("Pipeline complete (%d rows, %d cols)", *df.shape)
    return df
