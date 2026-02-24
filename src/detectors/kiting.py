"""Check-kiting detector for Fraudasaurus.ai.

Builds a directed transfer graph (accounts as nodes, transfers as edges)
and uses ``networkx.simple_cycles`` to find circular fund flows.
Cycles that complete within the typical check-clearing window (1--3 days)
are especially suspicious.

Scoring considers:
* Cycle length (shorter = more suspicious).
* Total dollar amount circulated.
* Frequency of the same cycle occurring.
* Whether multiple accounts in the cycle belong to the same customer.
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None  # type: ignore[assignment]
    logging.getLogger(__name__).warning(
        "networkx is not installed; KitingDetector will return empty results"
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_CYCLE_LENGTH: int = 10
_CLEARING_WINDOW_DAYS: int = 3

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
    "source_account": [
        "source_account", "from_account", "from_acct", "sender",
        "sender_account", "account_id", "acct_id",
    ],
    "dest_account": [
        "dest_account", "to_account", "destination_account", "recipient",
        "beneficiary", "recipient_id", "to_acct",
    ],
    "customer_id": [
        "customer_id", "cust_id", "owner_id", "customer",
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


def _require_column(df: pd.DataFrame, canonical: str) -> str:
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
    """Boolean mask for transfer-like transaction types."""
    normed = type_series.str.strip().str.lower()
    keywords = ["transfer", "wire", "ach", "eft", "send", "check", "cheque"]
    mask = normed.isin(keywords)
    for kw in keywords:
        mask = mask | normed.str.contains(kw, na=False)
    return mask


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class KitingDetector:
    """Detect check-kiting via cycle detection in the transfer graph.

    Parameters
    ----------
    max_cycle_length : int
        Maximum length of cycles to search for (default 10).
    clearing_window_days : int
        Number of days considered the "check-clearing" window (default 3).
        Cycles completed within this window score higher.
    """

    def __init__(
        self,
        max_cycle_length: int = _MAX_CYCLE_LENGTH,
        clearing_window_days: int = _CLEARING_WINDOW_DAYS,
    ) -> None:
        self.max_cycle_length = max_cycle_length
        self.clearing_window_days = clearing_window_days

    # ---- public API -------------------------------------------------------

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the kiting detector on a transactions DataFrame.

        The DataFrame must contain at least source and destination account
        columns (or ``account_id`` + ``recipient`` / ``dest_account``),
        a date column, and an amount column.

        Parameters
        ----------
        df : pd.DataFrame
            Transactions data.

        Returns
        -------
        pd.DataFrame
            Columns: ``account_id``, ``risk_score`` (0--1), ``flags``.
        """
        if nx is None:
            logger.error(
                "networkx is required for KitingDetector but is not installed"
            )
            return self._empty_result()

        if df.empty:
            logger.warning("Empty DataFrame passed to KitingDetector")
            return self._empty_result()

        # --- Resolve columns ------------------------------------------------
        src_col, dst_col, date_col, amt_col, type_col = (
            self._resolve_transfer_columns(df)
        )
        if src_col is None or dst_col is None:
            logger.warning(
                "KitingDetector: cannot identify source/dest account columns; "
                "returning empty results"
            )
            return self._empty_result()

        # --- Filter to transfers only ---------------------------------------
        work = df.copy()
        if type_col is not None:
            transfer_mask = _is_transfer(work[type_col].fillna(""))
            work = work[transfer_mask].copy()

        if work.empty:
            logger.info("No transfer transactions found")
            return self._empty_result()

        work[date_col] = _ensure_datetime(work[date_col])
        work[amt_col] = pd.to_numeric(work[amt_col], errors="coerce")
        work = work.dropna(subset=[src_col, dst_col, date_col, amt_col])

        if work.empty:
            logger.info("No valid transfer rows after cleaning")
            return self._empty_result()

        # Remove self-transfers
        work = work[work[src_col] != work[dst_col]]

        # --- Build directed graph -------------------------------------------
        G = nx.DiGraph()
        edge_data: Dict[Tuple[str, str], List[dict]] = defaultdict(list)

        for _, row in work.iterrows():
            src = str(row[src_col])
            dst = str(row[dst_col])
            G.add_edge(src, dst)
            edge_data[(src, dst)].append(
                {"date": row[date_col], "amount": row[amt_col]}
            )

        logger.info(
            "Transfer graph built: %d nodes, %d edges",
            G.number_of_nodes(),
            G.number_of_edges(),
        )

        # --- Find cycles ----------------------------------------------------
        try:
            raw_cycles = list(nx.simple_cycles(G, length_bound=self.max_cycle_length))
        except TypeError:
            # Older networkx versions do not support length_bound
            raw_cycles = [
                c for c in nx.simple_cycles(G)
                if len(c) <= self.max_cycle_length
            ]

        logger.info("Found %d cycle(s) in transfer graph", len(raw_cycles))

        if not raw_cycles:
            return self._empty_result()

        # Optionally resolve customer ownership for same-customer detection
        cust_col = _resolve_column(df, "customer_id")
        ownership: Dict[str, str] = {}
        if cust_col is not None and cust_col != src_col:
            for col in [src_col, dst_col]:
                pairs = df[[col, cust_col]].dropna().drop_duplicates()
                for _, row in pairs.iterrows():
                    ownership.setdefault(str(row[col]), str(row[cust_col]))

        # --- Score each cycle and accumulate per-account --------------------
        account_scores: Dict[str, float] = defaultdict(float)
        account_flags: Dict[str, List[str]] = defaultdict(list)

        for cycle in raw_cycles:
            score, flags = self._score_cycle(
                cycle, edge_data, ownership,
            )
            for acct in cycle:
                account_scores[acct] = max(account_scores[acct], score)
                account_flags[acct].extend(flags)

        # Deduplicate flags per account
        for acct in account_flags:
            account_flags[acct] = list(dict.fromkeys(account_flags[acct]))

        # Build result
        records = [
            {
                "account_id": acct,
                "risk_score": float(np.clip(score, 0.0, 1.0)),
                "flags": account_flags.get(acct, []),
            }
            for acct, score in account_scores.items()
            if score > 0
        ]

        if not records:
            return self._empty_result()

        result = (
            pd.DataFrame(records)
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True)
        )
        logger.info(
            "KitingDetector flagged %d accounts across %d cycle(s)",
            len(result),
            len(raw_cycles),
        )
        return result

    # ---- internal ---------------------------------------------------------

    def _resolve_transfer_columns(
        self, df: pd.DataFrame
    ) -> Tuple[Optional[str], Optional[str], str, str, Optional[str]]:
        """Attempt to find source, destination, date, amount, and type columns.

        Returns a 5-tuple ``(src_col, dst_col, date_col, amt_col, type_col)``.
        ``src_col`` or ``dst_col`` may be ``None`` if they cannot be
        identified.
        """
        # Try explicit source / dest first
        src_col = _resolve_column(df, "source_account")
        dst_col = _resolve_column(df, "dest_account")

        # If source resolves to the same column as dest (e.g., both hit
        # "account_id"), try harder to separate them.
        if src_col is not None and dst_col is not None and src_col == dst_col:
            src_col = _resolve_column(df, "account_id")
            # Try to find a separate recipient column
            dst_col = None
            for alias in ["recipient", "beneficiary", "to_account", "dest_account"]:
                for c in df.columns:
                    if alias.lower() == c.lower():
                        dst_col = c
                        break
                if dst_col is not None:
                    break

        date_col = _resolve_column(df, "transaction_date") or "transaction_date"
        amt_col = _resolve_column(df, "amount") or "amount"
        type_col = _resolve_column(df, "transaction_type")

        return src_col, dst_col, date_col, amt_col, type_col

    def _score_cycle(
        self,
        cycle: List[str],
        edge_data: Dict[Tuple[str, str], List[dict]],
        ownership: Dict[str, str],
    ) -> Tuple[float, List[str]]:
        """Compute a risk score for a single cycle.

        Returns ``(score, flags)`` where score is in [0, 1].
        """
        flags: List[str] = []
        sub_scores: List[float] = []

        cycle_len = len(cycle)

        # --- Length score: shorter cycles are more suspicious ---------------
        length_score = 1.0 - ((cycle_len - 2) / max(self.max_cycle_length - 2, 1))
        length_score = max(length_score, 0.1)
        sub_scores.append(length_score)

        # --- Timing: check if cycle completes within clearing window --------
        edges_in_cycle = []
        for i in range(cycle_len):
            src = cycle[i]
            dst = cycle[(i + 1) % cycle_len]
            edges_in_cycle.extend(edge_data.get((src, dst), []))

        if edges_in_cycle:
            dates = [e["date"] for e in edges_in_cycle if pd.notna(e["date"])]
            amounts = [e["amount"] for e in edges_in_cycle if pd.notna(e["amount"])]

            if dates:
                span = (max(dates) - min(dates)).total_seconds() / 86400.0
                if span <= self.clearing_window_days:
                    sub_scores.append(1.0)
                    flags.append(
                        f"Cycle of length {cycle_len} completed within "
                        f"{span:.1f} days (clearing window = "
                        f"{self.clearing_window_days}d)"
                    )
                else:
                    sub_scores.append(
                        max(0.0, 1.0 - (span - self.clearing_window_days) / 30.0)
                    )

            # --- Amount score -----------------------------------------------
            if amounts:
                total_circulated = sum(amounts)
                # Log-scale: $10K = ~0.4, $100K = ~0.7, $1M = 1.0
                amt_score = min(np.log10(max(total_circulated, 1)) / 6.0, 1.0)
                sub_scores.append(amt_score)
                flags.append(
                    f"${total_circulated:,.2f} circulated through "
                    f"{cycle_len}-account cycle: "
                    f"{' -> '.join(cycle[:5])}{'...' if cycle_len > 5 else ''}"
                )

            # --- Frequency: how many times does this cycle appear? ----------
            occurrence_count = min(len(edges_in_cycle) // max(cycle_len, 1), 10)
            if occurrence_count > 1:
                freq_score = min(occurrence_count / 5.0, 1.0)
                sub_scores.append(freq_score)
                flags.append(
                    f"Cycle pattern observed ~{occurrence_count} time(s)"
                )

        # --- Same-customer ownership ----------------------------------------
        if ownership:
            owners = [ownership.get(acct) for acct in cycle]
            owners_known = [o for o in owners if o is not None]
            if owners_known:
                unique_owners = set(owners_known)
                if len(unique_owners) == 1:
                    sub_scores.append(1.0)
                    flags.append(
                        f"All accounts in cycle owned by same customer "
                        f"({owners_known[0]})"
                    )
                elif len(unique_owners) < len(owners_known):
                    overlap_score = 1.0 - (
                        len(unique_owners) / len(owners_known)
                    )
                    sub_scores.append(overlap_score)
                    flags.append(
                        f"Overlapping ownership in cycle: "
                        f"{len(unique_owners)} unique customer(s) for "
                        f"{len(owners_known)} account(s)"
                    )

        # Combine
        if sub_scores:
            score = float(np.mean(sub_scores))
        else:
            score = 0.0

        return score, flags

    @staticmethod
    def _empty_result() -> pd.DataFrame:
        """Return an empty result DataFrame with the correct schema."""
        return pd.DataFrame(
            columns=["account_id", "risk_score", "flags"]
        ).astype({"risk_score": float})
