"""Structuring (smurfing) detector for Fraudasaurus.ai.

Detects patterns where customers split cash transactions to avoid the
$10,000 BSA/CTR reporting threshold.  Key signals include:

* Individual cash transactions in the $8,000--$9,999 range.
* Per-customer daily cash deposits that exceed $10K in aggregate but
  contain no single transaction above $10K.
* Repeated near-threshold deposits across 3+ days in a 7-day rolling
  window.
* Round-number amounts (ending in 00 or 000).

All signals are combined into a single 0--1 ``risk_score``.
"""

from __future__ import annotations

import logging
import re
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CTR_THRESHOLD: float = 10_000.0
_NEAR_LOW: float = 8_000.0
_NEAR_HIGH: float = 9_999.99
_ROLLING_WINDOW_DAYS: int = 7
_MIN_DAYS_IN_WINDOW: int = 3

# Column alias mappings (case-insensitive)
_COLUMN_ALIASES: dict[str, list[str]] = {
    "account_id": ["account_id", "acct_id", "account", "customer_id", "cust_id"],
    "transaction_date": [
        "transaction_date", "txn_date", "date", "timestamp", "trans_date",
    ],
    "amount": ["amount", "txn_amount", "transaction_amount", "value"],
    "transaction_type": [
        "transaction_type", "txn_type", "type", "trans_type",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_column(df: pd.DataFrame, canonical: str) -> str:
    """Return the actual column name in *df* that matches *canonical*.

    Searches alias list (case-insensitive), then falls back to substring
    regex.  Raises ``KeyError`` if nothing matches.
    """
    lower_cols = {c.lower(): c for c in df.columns}
    for alias in _COLUMN_ALIASES.get(canonical, [canonical]):
        if alias.lower() in lower_cols:
            return lower_cols[alias.lower()]

    pattern = re.compile(canonical.replace("_", ".*"), re.IGNORECASE)
    for col in df.columns:
        if pattern.search(col):
            return col

    raise KeyError(
        f"Could not resolve column '{canonical}' in {list(df.columns)}"
    )


def _ensure_datetime(series: pd.Series) -> pd.Series:
    """Coerce a Series to datetime if it is not already."""
    if not pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
    return series


def _is_cash_type(type_series: pd.Series) -> pd.Series:
    """Return a boolean mask for rows that look like cash transactions."""
    normed = type_series.str.strip().str.lower()
    cash_keywords = ["cash", "deposit", "dep", "credit", "cr", "atm"]
    return normed.isin(cash_keywords) | normed.str.contains("cash", na=False)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class StructuringDetector:
    """Detect cash-structuring patterns near the BSA/CTR $10K threshold.

    Parameters
    ----------
    near_low : float
        Lower bound of the "near-threshold" cash range (default 8000).
    near_high : float
        Upper bound of the "near-threshold" cash range (default 9999.99).
    rolling_days : int
        Size of the rolling window in calendar days (default 7).
    min_days : int
        Minimum distinct days with near-threshold deposits inside the
        rolling window to trigger the frequency flag (default 3).
    """

    def __init__(
        self,
        near_low: float = _NEAR_LOW,
        near_high: float = _NEAR_HIGH,
        rolling_days: int = _ROLLING_WINDOW_DAYS,
        min_days: int = _MIN_DAYS_IN_WINDOW,
    ) -> None:
        self.near_low = near_low
        self.near_high = near_high
        self.rolling_days = rolling_days
        self.min_days = min_days

    # ---- public API -------------------------------------------------------

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the structuring detector on a transactions DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain at least ``account_id``, ``transaction_date``, and
            ``amount`` columns (or close aliases).

        Returns
        -------
        pd.DataFrame
            Columns: ``account_id``, ``risk_score`` (0--1), ``flags``
            (list of human-readable explanation strings).
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to StructuringDetector")
            return self._empty_result()

        try:
            acct_col = _resolve_column(df, "account_id")
            date_col = _resolve_column(df, "transaction_date")
            amt_col = _resolve_column(df, "amount")
        except KeyError as exc:
            logger.error("StructuringDetector: %s", exc)
            return self._empty_result()

        # Attempt to resolve transaction_type for cash filtering; if missing,
        # treat ALL transactions as potential cash.
        try:
            type_col = _resolve_column(df, "transaction_type")
            has_type = True
        except KeyError:
            type_col = None
            has_type = False
            logger.info(
                "No transaction_type column found; treating all transactions "
                "as potentially cash-based"
            )

        work = df[[acct_col, date_col, amt_col]].copy()
        if has_type:
            work["_is_cash"] = _is_cash_type(df[type_col])
        else:
            work["_is_cash"] = True

        work[date_col] = _ensure_datetime(work[date_col])
        work["_date_only"] = work[date_col].dt.normalize()
        work[amt_col] = pd.to_numeric(work[amt_col], errors="coerce")
        work = work.dropna(subset=[acct_col, date_col, amt_col])

        # --- Signal 1: individual near-threshold transactions ---------------
        near_mask = (
            work["_is_cash"]
            & (work[amt_col] >= self.near_low)
            & (work[amt_col] <= self.near_high)
        )
        signal_near = (
            work[near_mask]
            .groupby(acct_col)[amt_col]
            .agg(near_count="count", near_max="max")
            .reset_index()
        )

        # Proximity to $10K (higher = closer = more suspicious)
        if not signal_near.empty:
            signal_near["proximity_score"] = (
                signal_near["near_max"] - self.near_low
            ) / (_CTR_THRESHOLD - self.near_low)
        else:
            signal_near["proximity_score"] = pd.Series(dtype=float)

        # --- Signal 2: daily aggregate > $10K with no single txn > $10K ----
        cash = work[work["_is_cash"]].copy()
        daily = cash.groupby([acct_col, "_date_only"]).agg(
            daily_total=(amt_col, "sum"),
            daily_max=(amt_col, "max"),
        ).reset_index()

        split_days = daily[
            (daily["daily_total"] > _CTR_THRESHOLD)
            & (daily["daily_max"] < _CTR_THRESHOLD)
        ]
        signal_split = (
            split_days.groupby(acct_col)
            .agg(split_day_count=("_date_only", "nunique"))
            .reset_index()
        )

        # --- Signal 3: rolling-window frequency ----------------------------
        near_days = (
            work[near_mask]
            .drop_duplicates(subset=[acct_col, "_date_only"])
            .sort_values([acct_col, "_date_only"])
        )

        rolling_hits: dict[str, int] = {}
        for acct, grp in near_days.groupby(acct_col):
            dates = grp["_date_only"].sort_values().reset_index(drop=True)
            max_count = 0
            for i in range(len(dates)):
                window_end = dates.iloc[i]
                window_start = window_end - pd.Timedelta(days=self.rolling_days - 1)
                count = ((dates >= window_start) & (dates <= window_end)).sum()
                if count > max_count:
                    max_count = count
            rolling_hits[acct] = max_count

        signal_rolling = pd.DataFrame(
            list(rolling_hits.items()),
            columns=[acct_col, "rolling_day_count"],
        )

        # --- Signal 4: round-number suspicion ------------------------------
        near_txns = work[near_mask].copy()
        near_txns["_is_round_100"] = (near_txns[amt_col] % 100 == 0).astype(int)
        near_txns["_is_round_1000"] = (near_txns[amt_col] % 1000 == 0).astype(int)
        signal_round = (
            near_txns.groupby(acct_col)
            .agg(
                round_100_count=("_is_round_100", "sum"),
                round_1000_count=("_is_round_1000", "sum"),
                total_near=("_is_round_100", "count"),
            )
            .reset_index()
        )
        if not signal_round.empty:
            signal_round["round_fraction"] = (
                signal_round["round_100_count"] / signal_round["total_near"]
            )
        else:
            signal_round["round_fraction"] = pd.Series(dtype=float)

        # --- Merge all signals ---------------------------------------------
        all_accts = pd.DataFrame({acct_col: work[acct_col].unique()})

        merged = all_accts.copy()
        for sig in [signal_near, signal_split, signal_rolling, signal_round]:
            if not sig.empty:
                merged = merged.merge(sig, on=acct_col, how="left")

        # Fill NaN with 0 for all numeric signal columns
        num_cols = merged.select_dtypes(include="number").columns
        merged[num_cols] = merged[num_cols].fillna(0.0)

        # --- Composite score -----------------------------------------------
        scores = pd.Series(0.0, index=merged.index)

        # Proximity (0-1), weighted at 30 %
        if "proximity_score" in merged.columns:
            scores += 0.30 * merged["proximity_score"].clip(0, 1)

        # Frequency of near-threshold days (rolling), weighted at 30 %
        if "rolling_day_count" in merged.columns:
            freq_score = (
                (merged["rolling_day_count"] - self.min_days + 1)
                .clip(0, None)
            )
            freq_score = (freq_score / freq_score.max()).fillna(0.0) if freq_score.max() > 0 else freq_score
            scores += 0.30 * freq_score

        # Split-day count, weighted at 25 %
        if "split_day_count" in merged.columns:
            split_score = merged["split_day_count"].clip(0, 10) / 10.0
            scores += 0.25 * split_score

        # Round-number fraction, weighted at 15 %
        if "round_fraction" in merged.columns:
            scores += 0.15 * merged["round_fraction"].clip(0, 1)

        merged["risk_score"] = scores.clip(0, 1)

        # --- Flags ---------------------------------------------------------
        merged["flags"] = merged.apply(
            lambda row: self._build_flags(row), axis=1
        )

        # Filter to only accounts with non-zero risk
        result = (
            merged[merged["risk_score"] > 0]
            [[acct_col, "risk_score", "flags"]]
            .rename(columns={acct_col: "account_id"})
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True)
        )

        logger.info(
            "StructuringDetector flagged %d / %d accounts",
            len(result),
            work[acct_col].nunique(),
        )
        return result

    # ---- internal ---------------------------------------------------------

    @staticmethod
    def _build_flags(row: pd.Series) -> List[str]:
        """Translate numeric signals into human-readable flag strings."""
        flags: List[str] = []

        near_count = row.get("near_count", 0)
        if near_count > 0:
            flags.append(
                f"{int(near_count)} cash transaction(s) in "
                f"$8K-$10K range (max ${row.get('near_max', 0):,.2f})"
            )

        split_days = row.get("split_day_count", 0)
        if split_days > 0:
            flags.append(
                f"Daily cash total exceeded $10K on {int(split_days)} day(s) "
                f"with no single txn over $10K (possible split deposits)"
            )

        rolling = row.get("rolling_day_count", 0)
        if rolling >= _MIN_DAYS_IN_WINDOW:
            flags.append(
                f"Near-threshold deposits on {int(rolling)} days within "
                f"a {_ROLLING_WINDOW_DAYS}-day window"
            )

        round_frac = row.get("round_fraction", 0)
        if round_frac > 0.5:
            flags.append(
                f"{round_frac:.0%} of near-threshold amounts are round numbers"
            )

        return flags

    @staticmethod
    def _empty_result() -> pd.DataFrame:
        """Return an empty result DataFrame with the correct schema."""
        return pd.DataFrame(
            columns=["account_id", "risk_score", "flags"]
        ).astype({"risk_score": float})
