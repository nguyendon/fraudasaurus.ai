"""Account-takeover (ATO) detector for Fraudasaurus.ai.

Identifies patterns consistent with a compromised account:

* Rapid profile changes (password, email, phone) followed by fund
  transfers.
* New device or channel usage that differs from the customer baseline.
* Unusual login hours compared to historical behaviour.
* Large outbound transfers to previously unseen recipients.

The detector degrades gracefully: if login / session columns are absent
the detector logs a warning and returns an empty result set rather than
raising an error.
"""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column alias mappings
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
    "channel": ["channel", "txn_channel", "source_channel", "medium"],
    "description": ["description", "desc", "memo", "narration", "details"],
    "device": ["device", "device_id", "device_type", "user_agent"],
    "recipient": [
        "recipient", "beneficiary", "to_account", "dest_account",
        "payee", "recipient_id",
    ],
    "event_type": [
        "event_type", "event", "action", "activity_type", "change_type",
    ],
    "login_time": [
        "login_time", "login_timestamp", "session_start", "login_at",
    ],
    "ip_address": ["ip_address", "ip", "source_ip", "client_ip"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_column(df: pd.DataFrame, canonical: str) -> Optional[str]:
    """Return the matching column name or ``None`` if not found.

    Unlike the strict version in ``features.py``, this returns ``None``
    so that the detector can degrade gracefully when optional columns are
    missing.
    """
    lower_cols = {c.lower(): c for c in df.columns}
    for alias in _COLUMN_ALIASES.get(canonical, [canonical]):
        if alias.lower() in lower_cols:
            return lower_cols[alias.lower()]

    pattern = re.compile(canonical.replace("_", ".*"), re.IGNORECASE)
    for col in df.columns:
        if pattern.search(col):
            return col

    return None


def _require_column(df: pd.DataFrame, canonical: str) -> str:
    """Like ``_resolve_column`` but raises ``KeyError`` on failure."""
    col = _resolve_column(df, canonical)
    if col is None:
        raise KeyError(
            f"Required column '{canonical}' not found in {list(df.columns)}"
        )
    return col


def _ensure_datetime(series: pd.Series) -> pd.Series:
    if not pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
    return series


def _is_transfer(type_series: pd.Series) -> pd.Series:
    """Return a boolean mask for transactions that look like fund transfers."""
    normed = type_series.str.strip().str.lower()
    keywords = [
        "transfer", "wire", "ach", "eft", "send", "payment",
        "withdrawal", "wd", "debit", "dr",
    ]
    mask = normed.isin(keywords)
    for kw in ["transfer", "wire", "ach", "send"]:
        mask = mask | normed.str.contains(kw, na=False)
    return mask


# ---------------------------------------------------------------------------
# Profile-change helpers
# ---------------------------------------------------------------------------

_PROFILE_CHANGE_KEYWORDS = [
    "password", "email", "phone", "address", "profile",
    "mfa", "2fa", "security", "credential",
]


def _is_profile_change(event_series: pd.Series) -> pd.Series:
    """Return a boolean mask for events that resemble profile changes."""
    normed = event_series.str.strip().str.lower()
    mask = pd.Series(False, index=event_series.index)
    for kw in _PROFILE_CHANGE_KEYWORDS:
        mask = mask | normed.str.contains(kw, na=False)
    return mask


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class AccountTakeoverDetector:
    """Detect account-takeover (ATO) patterns.

    Parameters
    ----------
    profile_transfer_window_hours : int
        Maximum time between a profile change and a subsequent transfer
        for the pair to be considered suspicious (default 48).
    unusual_hour_start : int
        Start of the "unusual hours" range (default 0 = midnight).
    unusual_hour_end : int
        End of the "unusual hours" range (default 5 = 5 AM).
    large_transfer_quantile : float
        Transfers above this per-account quantile are flagged as "large"
        (default 0.90).
    """

    def __init__(
        self,
        profile_transfer_window_hours: int = 48,
        unusual_hour_start: int = 0,
        unusual_hour_end: int = 5,
        large_transfer_quantile: float = 0.90,
    ) -> None:
        self.profile_transfer_window_hours = profile_transfer_window_hours
        self.unusual_hour_start = unusual_hour_start
        self.unusual_hour_end = unusual_hour_end
        self.large_transfer_quantile = large_transfer_quantile

    # ---- public API -------------------------------------------------------

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the account-takeover detector.

        Parameters
        ----------
        df : pd.DataFrame
            Transaction (and optionally event / login) data.

        Returns
        -------
        pd.DataFrame
            Columns: ``account_id``, ``risk_score`` (0--1), ``flags``.
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to AccountTakeoverDetector")
            return self._empty_result()

        # Resolve required columns
        acct_col = _resolve_column(df, "account_id")
        date_col = _resolve_column(df, "transaction_date")
        amt_col = _resolve_column(df, "amount")

        if acct_col is None or date_col is None or amt_col is None:
            missing = [
                name
                for name, col in [
                    ("account_id", acct_col),
                    ("transaction_date", date_col),
                    ("amount", amt_col),
                ]
                if col is None
            ]
            logger.warning(
                "AccountTakeoverDetector: required columns missing (%s); "
                "returning empty results",
                ", ".join(missing),
            )
            return self._empty_result()

        # Resolve optional columns
        type_col = _resolve_column(df, "transaction_type")
        channel_col = _resolve_column(df, "channel")
        device_col = _resolve_column(df, "device")
        recipient_col = _resolve_column(df, "recipient")
        event_col = _resolve_column(df, "event_type")

        # Prepare working copy
        work = df.copy()
        work[date_col] = _ensure_datetime(work[date_col])
        work[amt_col] = pd.to_numeric(work[amt_col], errors="coerce")
        work = work.dropna(subset=[acct_col, date_col, amt_col])

        if work.empty:
            logger.warning("No valid rows after cleaning; returning empty results")
            return self._empty_result()

        # Collect per-account signals
        accounts = work[acct_col].unique()
        records: List[Dict] = []

        for acct in accounts:
            acct_data = work[work[acct_col] == acct].sort_values(date_col)
            flags: List[str] = []
            sub_scores: List[float] = []

            # -- Signal 1: profile changes followed by transfers -------------
            if event_col is not None:
                profile_score, profile_flags = self._score_profile_then_transfer(
                    acct_data, date_col, amt_col, event_col, type_col,
                )
                sub_scores.append(profile_score)
                flags.extend(profile_flags)

            # -- Signal 2: new / unusual channel or device -------------------
            channel_score, channel_flags = self._score_channel_device(
                acct_data, date_col, channel_col, device_col,
            )
            sub_scores.append(channel_score)
            flags.extend(channel_flags)

            # -- Signal 3: unusual login hours (using transaction timestamp) -
            hour_score, hour_flags = self._score_unusual_hours(
                acct_data, date_col,
            )
            sub_scores.append(hour_score)
            flags.extend(hour_flags)

            # -- Signal 4: large transfer to new recipient -------------------
            if type_col is not None and recipient_col is not None:
                recip_score, recip_flags = self._score_new_recipient_transfer(
                    acct_data, date_col, amt_col, type_col, recipient_col,
                )
                sub_scores.append(recip_score)
                flags.extend(recip_flags)

            # Combine
            if sub_scores:
                risk_score = float(np.clip(np.mean(sub_scores), 0.0, 1.0))
            else:
                risk_score = 0.0

            if risk_score > 0 and flags:
                records.append(
                    {
                        "account_id": acct,
                        "risk_score": risk_score,
                        "flags": flags,
                    }
                )

        if not records:
            logger.info("AccountTakeoverDetector: no accounts flagged")
            return self._empty_result()

        result = (
            pd.DataFrame(records)
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True)
        )
        logger.info(
            "AccountTakeoverDetector flagged %d / %d accounts",
            len(result),
            len(accounts),
        )
        return result

    # ---- scoring helpers --------------------------------------------------

    def _score_profile_then_transfer(
        self,
        acct_data: pd.DataFrame,
        date_col: str,
        amt_col: str,
        event_col: str,
        type_col: Optional[str],
    ) -> tuple[float, List[str]]:
        """Score the pattern of profile change followed quickly by transfer."""
        flags: List[str] = []

        profile_mask = _is_profile_change(acct_data[event_col].fillna(""))
        profile_changes = acct_data[profile_mask]

        if type_col is not None:
            transfer_mask = _is_transfer(acct_data[type_col].fillna(""))
        else:
            # If no type column, consider all outgoing amounts as potential
            transfer_mask = acct_data[amt_col] > 0

        transfers = acct_data[transfer_mask]

        if profile_changes.empty or transfers.empty:
            return 0.0, flags

        window = timedelta(hours=self.profile_transfer_window_hours)
        suspicious_count = 0

        for _, pc_row in profile_changes.iterrows():
            pc_time = pc_row[date_col]
            close_transfers = transfers[
                (transfers[date_col] > pc_time)
                & (transfers[date_col] <= pc_time + window)
            ]
            if not close_transfers.empty:
                suspicious_count += 1
                max_amt = close_transfers[amt_col].max()
                flags.append(
                    f"Profile change at {pc_time} followed by transfer "
                    f"(max ${max_amt:,.2f}) within {self.profile_transfer_window_hours}h"
                )

        score = min(suspicious_count / 3.0, 1.0)
        return score, flags

    def _score_channel_device(
        self,
        acct_data: pd.DataFrame,
        date_col: str,
        channel_col: Optional[str],
        device_col: Optional[str],
    ) -> tuple[float, List[str]]:
        """Score the use of new channels or devices in the recent window."""
        flags: List[str] = []
        scores: List[float] = []

        for col, label in [(channel_col, "channel"), (device_col, "device")]:
            if col is None or col not in acct_data.columns:
                continue

            values = acct_data[col].dropna()
            if len(values) < 2:
                continue

            # Consider the last 20 % of rows as "recent"
            split = max(1, int(len(values) * 0.8))
            historical = set(values.iloc[:split].str.lower())
            recent = set(values.iloc[split:].str.lower())
            new_vals = recent - historical

            if new_vals and historical:
                ratio = len(new_vals) / max(len(recent), 1)
                scores.append(ratio)
                flags.append(
                    f"New {label}(s) in recent activity: {', '.join(sorted(new_vals))}"
                )

        if scores:
            return float(np.mean(scores)), flags
        return 0.0, flags

    def _score_unusual_hours(
        self,
        acct_data: pd.DataFrame,
        date_col: str,
    ) -> tuple[float, List[str]]:
        """Score the fraction of recent transactions in unusual hours."""
        flags: List[str] = []

        hours = acct_data[date_col].dt.hour
        if hours.empty:
            return 0.0, flags

        unusual_mask = (hours >= self.unusual_hour_start) & (
            hours <= self.unusual_hour_end
        )

        # Look at the last 20 % of activity
        split = max(1, int(len(hours) * 0.8))
        recent_unusual_frac = unusual_mask.iloc[split:].mean()
        historical_unusual_frac = unusual_mask.iloc[:split].mean()

        # Only flag if recent unusual fraction is significantly elevated
        if recent_unusual_frac > 0.3 and recent_unusual_frac > historical_unusual_frac * 2:
            flags.append(
                f"{recent_unusual_frac:.0%} of recent activity during "
                f"unusual hours ({self.unusual_hour_start}:00-"
                f"{self.unusual_hour_end}:00)"
            )
            return float(min(recent_unusual_frac, 1.0)), flags

        return 0.0, flags

    def _score_new_recipient_transfer(
        self,
        acct_data: pd.DataFrame,
        date_col: str,
        amt_col: str,
        type_col: str,
        recipient_col: str,
    ) -> tuple[float, List[str]]:
        """Score large transfers to previously unseen recipients."""
        flags: List[str] = []

        transfers = acct_data[_is_transfer(acct_data[type_col].fillna(""))].copy()
        if transfers.empty or recipient_col not in transfers.columns:
            return 0.0, flags

        recipients = transfers[recipient_col].dropna()
        if len(recipients) < 2:
            return 0.0, flags

        # Historical vs recent split
        split = max(1, int(len(transfers) * 0.8))
        historical_recips = set(
            transfers.iloc[:split][recipient_col].dropna().str.lower()
        )
        recent = transfers.iloc[split:]
        recent_recips = recent[recipient_col].dropna().str.lower()

        # Large transfer threshold
        all_amounts = transfers[amt_col].dropna()
        if all_amounts.empty:
            return 0.0, flags
        threshold = all_amounts.quantile(self.large_transfer_quantile)

        new_recip_large = recent[
            (recent_recips.isin(historical_recips) == False)  # noqa: E712
            & (recent[amt_col] >= threshold)
        ]

        if not new_recip_large.empty:
            total = new_recip_large[amt_col].sum()
            flags.append(
                f"${total:,.2f} transferred to {len(new_recip_large)} "
                f"new recipient(s) above {self.large_transfer_quantile:.0%} "
                f"historical threshold (${threshold:,.2f})"
            )
            score = min(len(new_recip_large) / 3.0, 1.0)
            return score, flags

        return 0.0, flags

    # ---- utility ----------------------------------------------------------

    @staticmethod
    def _empty_result() -> pd.DataFrame:
        """Return an empty result DataFrame with the correct schema."""
        return pd.DataFrame(
            columns=["account_id", "risk_score", "flags"]
        ).astype({"risk_score": float})
