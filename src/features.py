"""Feature engineering module for Fraudasaurus.ai.

Builds per-account behavioural features from a transactions DataFrame.
Each function accepts a DataFrame and returns features indexed by account_id.
The ``build_feature_matrix`` function orchestrates all of them into a single
feature matrix ready for downstream detectors.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column resolution helpers
# ---------------------------------------------------------------------------

_COLUMN_ALIASES: dict[str, list[str]] = {
    "account_id": ["account_id", "acct_id", "account", "customer_id"],
    "transaction_date": ["transaction_date", "txn_date", "date", "timestamp", "trans_date"],
    "amount": ["amount", "txn_amount", "transaction_amount", "value"],
    "transaction_type": ["transaction_type", "txn_type", "type", "trans_type"],
    "channel": ["channel", "txn_channel", "source_channel", "medium"],
}


def _resolve_column(df: pd.DataFrame, canonical: str) -> str:
    """Return the actual column name in *df* that matches *canonical*.

    Tries the alias list first (case-insensitive), then falls back to a
    regex search for a partial match.  Raises ``KeyError`` if nothing works.
    """
    lower_cols = {c.lower(): c for c in df.columns}
    for alias in _COLUMN_ALIASES.get(canonical, [canonical]):
        if alias.lower() in lower_cols:
            return lower_cols[alias.lower()]

    # Fallback: substring match
    pattern = re.compile(canonical.replace("_", ".*"), re.IGNORECASE)
    for col in df.columns:
        if pattern.search(col):
            return col

    raise KeyError(
        f"Could not find a column matching '{canonical}' in {list(df.columns)}"
    )


def _ensure_datetime(series: pd.Series) -> pd.Series:
    """Coerce a Series to datetime if it isn't already."""
    if not pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
    return series


# ---------------------------------------------------------------------------
# Individual feature builders
# ---------------------------------------------------------------------------


def transaction_velocity(
    df: pd.DataFrame,
    window: str = "7D",
) -> pd.DataFrame:
    """Count of transactions per account in a rolling time window.

    Returns a DataFrame with columns ``[account_id, txn_velocity_{window}]``.
    The value is the maximum rolling count observed in the window for each
    account (a single summary number per account).
    """
    acct_col = _resolve_column(df, "account_id")
    date_col = _resolve_column(df, "transaction_date")

    tmp = df[[acct_col, date_col]].copy()
    tmp[date_col] = _ensure_datetime(tmp[date_col])
    tmp = tmp.sort_values([acct_col, date_col])

    # Rolling count per account
    tmp["_ones"] = 1
    tmp = tmp.set_index(date_col)

    col_name = f"txn_velocity_{window}"
    result = (
        tmp.groupby(acct_col)["_ones"]
        .rolling(window)
        .sum()
        .reset_index()
        .groupby(acct_col)["_ones"]
        .max()
        .rename(col_name)
        .reset_index()
    )
    result = result.rename(columns={acct_col: "account_id"})
    logger.info("Computed transaction velocity (window=%s)", window)
    return result


def amount_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-account mean, max, and standard deviation of transaction amounts.

    Returns columns: ``[account_id, amount_mean, amount_max, amount_std]``.
    """
    acct_col = _resolve_column(df, "account_id")
    amt_col = _resolve_column(df, "amount")

    agg = (
        df.groupby(acct_col)[amt_col]
        .agg(amount_mean="mean", amount_max="max", amount_std="std")
        .reset_index()
        .rename(columns={acct_col: "account_id"})
    )
    agg["amount_std"] = agg["amount_std"].fillna(0.0)
    logger.info("Computed amount statistics")
    return agg


def channel_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """Per-account count of unique transaction channels.

    Returns columns: ``[account_id, channel_diversity]``.
    """
    acct_col = _resolve_column(df, "account_id")
    chan_col = _resolve_column(df, "channel")

    result = (
        df.groupby(acct_col)[chan_col]
        .nunique()
        .rename("channel_diversity")
        .reset_index()
        .rename(columns={acct_col: "account_id"})
    )
    logger.info("Computed channel diversity")
    return result


def time_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Per-account temporal behaviour features.

    Returns columns:
        * ``weekend_fraction``  -- share of transactions on Sat/Sun
        * ``late_night_fraction`` -- share of transactions between 22:00 and 06:00
    """
    acct_col = _resolve_column(df, "account_id")
    date_col = _resolve_column(df, "transaction_date")

    tmp = df[[acct_col, date_col]].copy()
    tmp[date_col] = _ensure_datetime(tmp[date_col])

    tmp["_is_weekend"] = tmp[date_col].dt.dayofweek.isin([5, 6]).astype(int)
    hour = tmp[date_col].dt.hour
    tmp["_is_late_night"] = ((hour >= 22) | (hour < 6)).astype(int)

    result = (
        tmp.groupby(acct_col)
        .agg(
            weekend_fraction=("_is_weekend", "mean"),
            late_night_fraction=("_is_late_night", "mean"),
        )
        .reset_index()
        .rename(columns={acct_col: "account_id"})
    )
    logger.info("Computed time patterns")
    return result


def deposit_withdrawal_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Per-account ratio of total deposit amount to total withdrawal amount.

    Accounts with zero withdrawals receive a ratio of ``NaN`` which is then
    filled with 0.0 (indicating no withdrawal activity).

    Returns columns: ``[account_id, deposit_withdrawal_ratio]``.
    """
    acct_col = _resolve_column(df, "account_id")
    amt_col = _resolve_column(df, "amount")
    type_col = _resolve_column(df, "transaction_type")

    tmp = df[[acct_col, amt_col, type_col]].copy()
    tmp[type_col] = tmp[type_col].str.strip().str.lower()

    deposits = (
        tmp[tmp[type_col].isin(["deposit", "dep", "credit", "cr"])]
        .groupby(acct_col)[amt_col]
        .sum()
        .rename("_dep_total")
    )
    withdrawals = (
        tmp[tmp[type_col].isin(["withdrawal", "wd", "debit", "dr", "withdraw"])]
        .groupby(acct_col)[amt_col]
        .sum()
        .rename("_wd_total")
    )

    combined = pd.concat([deposits, withdrawals], axis=1).fillna(0.0)
    combined["deposit_withdrawal_ratio"] = combined["_dep_total"] / combined["_wd_total"].replace(0, float("nan"))
    combined["deposit_withdrawal_ratio"] = combined["deposit_withdrawal_ratio"].fillna(0.0)

    result = (
        combined[["deposit_withdrawal_ratio"]]
        .reset_index()
        .rename(columns={acct_col: "account_id"})
    )
    logger.info("Computed deposit/withdrawal ratio")
    return result


# ---------------------------------------------------------------------------
# Unified feature matrix
# ---------------------------------------------------------------------------


def build_feature_matrix(df: pd.DataFrame, velocity_window: str = "7D") -> pd.DataFrame:
    """Build a single feature DataFrame by merging all feature builders.

    Calls every individual feature function and left-joins the results on
    ``account_id``.

    Args:
        df: Transactions DataFrame (must contain account_id, transaction_date,
            amount, transaction_type, and channel columns -- or close aliases).
        velocity_window: Rolling window string passed to ``transaction_velocity``.

    Returns:
        DataFrame indexed by ``account_id`` with all engineered features.
    """
    builders = [
        transaction_velocity(df, window=velocity_window),
        amount_stats(df),
        channel_diversity(df),
        time_patterns(df),
        deposit_withdrawal_ratio(df),
    ]

    matrix = builders[0]
    for feat_df in builders[1:]:
        matrix = matrix.merge(feat_df, on="account_id", how="outer")

    matrix = matrix.set_index("account_id").sort_index()
    logger.info(
        "Feature matrix built: %d accounts x %d features",
        matrix.shape[0],
        matrix.shape[1],
    )
    return matrix
