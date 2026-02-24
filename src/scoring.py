"""Risk scoring engine — combine alerts from all detectors into per-account risk scores."""

from __future__ import annotations

import pandas as pd

SEVERITY_POINTS = {
    "CRITICAL": 40,
    "HIGH": 25,
    "MEDIUM": 10,
    "LOW": 5,
}

TIER_THRESHOLDS = [
    (80, "CRITICAL"),
    (50, "HIGH"),
    (25, "MEDIUM"),
    (1, "LOW"),
]


def score_alerts(alerts: list[dict]) -> pd.DataFrame:
    """Combine alerts, sum scores per account, cap at 100, assign tiers.

    Returns a DataFrame with one row per account, sorted by composite score descending.
    """
    if not alerts:
        return pd.DataFrame(columns=[
            "account_id", "user_id", "member_number", "composite_score",
            "tier", "fraud_types", "alert_count", "evidence_summary",
        ])

    df = pd.DataFrame(alerts)

    # Use best available identifier for grouping
    df["group_key"] = df.apply(_group_key, axis=1)

    grouped = df.groupby("group_key").agg(
        account_id=("account_id", "first"),
        user_id=("user_id", "first"),
        member_number=("member_number", "first"),
        composite_score=("score", "sum"),
        fraud_types=("fraud_type", lambda x: ", ".join(sorted(set(x)))),
        alert_count=("fraud_type", "size"),
        evidence_summary=("evidence", lambda x: " | ".join(x)),
    ).reset_index(drop=True)

    # Cap at 100
    grouped["composite_score"] = grouped["composite_score"].clip(upper=100)

    # Assign tier
    grouped["tier"] = grouped["composite_score"].apply(_assign_tier)

    # Sort by score descending
    grouped = grouped.sort_values("composite_score", ascending=False).reset_index(drop=True)

    return grouped


def _group_key(row: pd.Series) -> str:
    """Pick the best identifier to group alerts by."""
    if row.get("account_id"):
        return f"acct:{row['account_id']}"
    if row.get("user_id"):
        return f"user:{row['user_id']}"
    if row.get("member_number"):
        return f"member:{row['member_number']}"
    return f"unknown:{id(row)}"


def _assign_tier(score: int) -> str:
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "LOW"
