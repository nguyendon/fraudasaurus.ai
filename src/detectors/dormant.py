"""Dormant-account reactivation detector for Fraudasaurus.ai.

Identifies accounts that have been inactive for an extended period and
then suddenly resume activity -- a pattern commonly associated with
account compromise, money-mule recruitment, or shell-account activation.

Key signals:
* 90+ days of no transactions followed by sudden activity.
* First transaction back is large relative to historical average (>3x).
* Rapid deposit-then-withdrawal pattern after reactivation.
* Profile changes on a dormant account.
* Coordinated reactivation: multiple dormant accounts activated within
  the same 7-day window.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DORMANCY_DAYS: int = 90
_LARGE_TXN_MULTIPLIER: float = 3.0
_RAPID_WITHDRAWAL_DAYS: int = 3
_COORDINATED_WINDOW_DAYS: int = 7

# ---------------------------------------------------------------------------
# Column aliases
# ---------------------------------------------------------------------------

_COLUMN_ALIASES: dict[str, list[str]] = {
    "account_id": ["account_id", "acct_id", "account", "customer_id", "cust_id"],
    "transaction_date": [
        "transaction_date", "txn_date", "date", "timestamp", "trans_date",
    ],
    "amount": ["amount", "txn_amount", "transaction_amount", "value"],
    "transaction_type": [
        "transaction_type", "txn_type", "type", "trans_type",
    ],
    "event_type": [
        "event_type", "event", "action", "activity_type", "change_type",
    ],
}


def _resolve_column(df: pd.DataFrame, canonical: str) -> Optional[str]:
    """Return the matching column name or ``None``."""
    lower_cols = {c.lower(): c for c in df.columns}
    for alias in _COLUMN_ALIASES.get(canonical, [canonical]):
        if alias.lower() in lower_cols:
            return lower_cols[alias.lower()]

    pattern = re.compile(canonical.replace("_", ".*"), re.IGNORECASE)
    for col in df.columns:
        if pattern.search(col):
            return col
    return None


def _ensure_datetime(series: pd.Series) -> pd.Series:
    if not pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
    return series


def _is_deposit(type_series: pd.Series) -> pd.Series:
    """Boolean mask for deposit-like transaction types."""
    normed = type_series.str.strip().str.lower()
    return normed.isin(["deposit", "dep", "credit", "cr", "cash"]) | normed.str.contains(
        "deposit|credit", na=False
    )


def _is_withdrawal(type_series: pd.Series) -> pd.Series:
    """Boolean mask for withdrawal-like transaction types."""
    normed = type_series.str.strip().str.lower()
    return normed.isin([
        "withdrawal", "wd", "debit", "dr", "withdraw", "transfer",
        "wire", "ach", "send",
    ]) | normed.str.contains("withdraw|debit|wire|transfer", na=False)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class DormantAccountDetector:
    """Detect suspicious reactivation of dormant accounts.

    Parameters
    ----------
    dormancy_days : int
        Number of consecutive inactive days to classify an account as
        dormant (default 90).
    large_txn_multiplier : float
        If the first transaction after reactivation exceeds the
        historical average by this factor, flag it (default 3.0).
    rapid_withdrawal_days : int
        Maximum days between a deposit and a subsequent withdrawal for
        the pair to be considered a rapid deposit-then-withdrawal
        pattern (default 3).
    coordinated_window_days : int
        Window in which multiple dormant reactivations are considered
        coordinated (default 7).
    """

    def __init__(
        self,
        dormancy_days: int = _DORMANCY_DAYS,
        large_txn_multiplier: float = _LARGE_TXN_MULTIPLIER,
        rapid_withdrawal_days: int = _RAPID_WITHDRAWAL_DAYS,
        coordinated_window_days: int = _COORDINATED_WINDOW_DAYS,
    ) -> None:
        self.dormancy_days = dormancy_days
        self.large_txn_multiplier = large_txn_multiplier
        self.rapid_withdrawal_days = rapid_withdrawal_days
        self.coordinated_window_days = coordinated_window_days

    # ---- public API -------------------------------------------------------

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the dormant-account detector.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain at least ``account_id``, ``transaction_date``,
            and ``amount`` columns (or close aliases).

        Returns
        -------
        pd.DataFrame
            Columns: ``account_id``, ``risk_score`` (0--1), ``flags``.
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to DormantAccountDetector")
            return self._empty_result()

        # Resolve columns
        acct_col = _resolve_column(df, "account_id")
        date_col = _resolve_column(df, "transaction_date")
        amt_col = _resolve_column(df, "amount")

        if acct_col is None or date_col is None or amt_col is None:
            missing = [
                name for name, col in [
                    ("account_id", acct_col),
                    ("transaction_date", date_col),
                    ("amount", amt_col),
                ] if col is None
            ]
            logger.error(
                "DormantAccountDetector: required columns missing (%s)",
                ", ".join(missing),
            )
            return self._empty_result()

        type_col = _resolve_column(df, "transaction_type")
        event_col = _resolve_column(df, "event_type")

        # Prepare work copy
        work = df.copy()
        work[date_col] = _ensure_datetime(work[date_col])
        work[amt_col] = pd.to_numeric(work[amt_col], errors="coerce")
        work = work.dropna(subset=[acct_col, date_col, amt_col])
        work = work.sort_values([acct_col, date_col])

        if work.empty:
            return self._empty_result()

        # --- Identify dormant-then-reactivated accounts ---------------------
        dormant_accounts = self._find_dormant_reactivations(
            work, acct_col, date_col, amt_col
        )

        if not dormant_accounts:
            logger.info("No dormant-account reactivations found")
            return self._empty_result()

        # --- Score each dormant account -------------------------------------
        records: List[Dict] = []
        reactivation_dates: Dict[str, pd.Timestamp] = {}

        for acct, info in dormant_accounts.items():
            flags: List[str] = []
            sub_scores: List[float] = []

            acct_data = work[work[acct_col] == acct].sort_values(date_col)
            dormancy_gap = info["dormancy_days"]
            reactivation_date = info["reactivation_date"]
            reactivation_dates[acct] = reactivation_date

            # Signal 1: dormancy duration
            duration_score = min(dormancy_gap / (self.dormancy_days * 4), 1.0)
            sub_scores.append(duration_score)
            flags.append(
                f"Account dormant for {dormancy_gap} days before "
                f"reactivation on {reactivation_date.strftime('%Y-%m-%d')}"
            )

            # Signal 2: large first-back transaction
            first_back_amt = info["first_back_amount"]
            hist_avg = info["historical_avg"]
            if hist_avg > 0 and first_back_amt > hist_avg * self.large_txn_multiplier:
                ratio = first_back_amt / hist_avg
                size_score = min(ratio / (self.large_txn_multiplier * 3), 1.0)
                sub_scores.append(size_score)
                flags.append(
                    f"First transaction after reactivation "
                    f"(${first_back_amt:,.2f}) is {ratio:.1f}x the "
                    f"historical average (${hist_avg:,.2f})"
                )

            # Signal 3: rapid deposit-then-withdrawal
            if type_col is not None:
                dw_score, dw_flags = self._score_rapid_deposit_withdrawal(
                    acct_data, date_col, amt_col, type_col, reactivation_date,
                )
                if dw_score > 0:
                    sub_scores.append(dw_score)
                    flags.extend(dw_flags)

            # Signal 4: profile changes on dormant account
            if event_col is not None:
                pc_score, pc_flags = self._score_profile_changes(
                    acct_data, date_col, event_col, reactivation_date,
                    dormancy_gap,
                )
                if pc_score > 0:
                    sub_scores.append(pc_score)
                    flags.extend(pc_flags)

            risk_score = float(np.clip(np.mean(sub_scores), 0.0, 1.0))
            records.append({
                "account_id": acct,
                "risk_score": risk_score,
                "flags": flags,
            })

        # --- Signal 5: coordinated reactivation bonus ----------------------
        records = self._apply_coordinated_bonus(records, reactivation_dates)

        if not records:
            return self._empty_result()

        result = (
            pd.DataFrame(records)
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True)
        )
        logger.info(
            "DormantAccountDetector flagged %d / %d accounts",
            len(result),
            work[acct_col].nunique(),
        )
        return result

    # ---- internal helpers -------------------------------------------------

    def _find_dormant_reactivations(
        self,
        work: pd.DataFrame,
        acct_col: str,
        date_col: str,
        amt_col: str,
    ) -> Dict[str, Dict]:
        """Identify accounts with gaps >= ``dormancy_days`` between
        consecutive transactions.

        Returns a dict mapping account -> info dict with keys:
            dormancy_days, reactivation_date, first_back_amount,
            historical_avg.
        """
        dormant: Dict[str, Dict] = {}

        for acct, grp in work.groupby(acct_col):
            grp = grp.sort_values(date_col)
            dates = grp[date_col].reset_index(drop=True)
            amounts = grp[amt_col].reset_index(drop=True)

            if len(dates) < 2:
                continue

            # Compute gaps between consecutive transactions
            gaps = dates.diff().dt.days
            max_gap_idx = gaps.idxmax()

            if pd.isna(gaps.iloc[max_gap_idx]):
                continue

            max_gap = int(gaps.iloc[max_gap_idx])

            if max_gap >= self.dormancy_days:
                # Historical average = average of transactions before the gap
                pre_gap = amounts.iloc[:max_gap_idx]
                hist_avg = float(pre_gap.abs().mean()) if len(pre_gap) > 0 else 0.0
                first_back = float(abs(amounts.iloc[max_gap_idx]))

                dormant[str(acct)] = {
                    "dormancy_days": max_gap,
                    "reactivation_date": dates.iloc[max_gap_idx],
                    "first_back_amount": first_back,
                    "historical_avg": hist_avg,
                }

        return dormant

    def _score_rapid_deposit_withdrawal(
        self,
        acct_data: pd.DataFrame,
        date_col: str,
        amt_col: str,
        type_col: str,
        reactivation_date: pd.Timestamp,
    ) -> Tuple[float, List[str]]:
        """Score rapid deposit-then-withdrawal pattern after reactivation."""
        flags: List[str] = []

        post = acct_data[acct_data[date_col] >= reactivation_date].copy()
        if post.empty or type_col not in post.columns:
            return 0.0, flags

        type_series = post[type_col].fillna("")
        deposits = post[_is_deposit(type_series)]
        withdrawals = post[_is_withdrawal(type_series)]

        if deposits.empty or withdrawals.empty:
            return 0.0, flags

        rapid_pairs = 0
        total_rapid_amount = 0.0
        window = pd.Timedelta(days=self.rapid_withdrawal_days)

        for _, dep_row in deposits.iterrows():
            dep_date = dep_row[date_col]
            dep_amt = dep_row[amt_col]
            close_wd = withdrawals[
                (withdrawals[date_col] > dep_date)
                & (withdrawals[date_col] <= dep_date + window)
            ]
            if not close_wd.empty:
                rapid_pairs += 1
                total_rapid_amount += close_wd[amt_col].sum()

        if rapid_pairs > 0:
            score = min(rapid_pairs / 3.0, 1.0)
            flags.append(
                f"{rapid_pairs} deposit-then-withdrawal pair(s) within "
                f"{self.rapid_withdrawal_days} days after reactivation "
                f"(${total_rapid_amount:,.2f} withdrawn)"
            )
            return score, flags

        return 0.0, flags

    def _score_profile_changes(
        self,
        acct_data: pd.DataFrame,
        date_col: str,
        event_col: str,
        reactivation_date: pd.Timestamp,
        dormancy_gap: int,
    ) -> Tuple[float, List[str]]:
        """Score profile changes during or just before reactivation."""
        flags: List[str] = []

        if event_col not in acct_data.columns:
            return 0.0, flags

        events = acct_data[event_col].fillna("").str.lower()
        profile_keywords = [
            "password", "email", "phone", "address", "profile",
            "mfa", "2fa", "security",
        ]

        profile_mask = pd.Series(False, index=events.index)
        for kw in profile_keywords:
            profile_mask = profile_mask | events.str.contains(kw, na=False)

        # Look at the dormancy period and first week after reactivation
        dormancy_start = reactivation_date - pd.Timedelta(days=dormancy_gap)
        window_end = reactivation_date + pd.Timedelta(days=7)

        changes_in_window = acct_data[
            profile_mask
            & (acct_data[date_col] >= dormancy_start)
            & (acct_data[date_col] <= window_end)
        ]

        if not changes_in_window.empty:
            count = len(changes_in_window)
            score = min(count / 3.0, 1.0)
            flags.append(
                f"{count} profile change(s) on dormant/reactivating account"
            )
            return score, flags

        return 0.0, flags

    def _apply_coordinated_bonus(
        self,
        records: List[Dict],
        reactivation_dates: Dict[str, pd.Timestamp],
    ) -> List[Dict]:
        """Boost scores when multiple dormant accounts reactivate within
        the same time window (coordinated reactivation)."""
        if len(reactivation_dates) < 2:
            return records

        # Sort reactivation dates
        sorted_dates = sorted(reactivation_dates.items(), key=lambda x: x[1])
        window = pd.Timedelta(days=self.coordinated_window_days)

        # Find clusters of reactivations
        clusters: List[List[str]] = []
        current_cluster: List[str] = [sorted_dates[0][0]]
        cluster_start = sorted_dates[0][1]

        for acct, dt in sorted_dates[1:]:
            if dt - cluster_start <= window:
                current_cluster.append(acct)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [acct]
                cluster_start = dt

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        # Build set of coordinated accounts for fast lookup
        coordinated_accounts: set = set()
        cluster_sizes: Dict[str, int] = {}
        for cluster in clusters:
            for acct in cluster:
                coordinated_accounts.add(acct)
                cluster_sizes[acct] = len(cluster)

        # Apply bonus
        for record in records:
            acct = record["account_id"]
            if acct in coordinated_accounts:
                size = cluster_sizes[acct]
                bonus = min(size * 0.1, 0.3)
                record["risk_score"] = float(
                    np.clip(record["risk_score"] + bonus, 0.0, 1.0)
                )
                record["flags"].append(
                    f"Coordinated reactivation: {size} dormant accounts "
                    f"activated within {self.coordinated_window_days}-day window"
                )

        return records

    @staticmethod
    def _empty_result() -> pd.DataFrame:
        """Return an empty result DataFrame with the correct schema."""
        return pd.DataFrame(
            columns=["account_id", "risk_score", "flags"]
        ).astype({"risk_score": float})
