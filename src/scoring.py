"""Unified risk scoring module for Fraudasaurus.ai.

Aggregates risk scores produced by individual detectors into a single
composite score per account, assigns risk tiers, and identifies which
detectors triggered for each account.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_THRESHOLDS: dict[str, float] = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
    # CRITICAL = anything above HIGH threshold
}

DEFAULT_WEIGHTS: dict[str, float] = {
    "structuring": 1.0,
    "account_takeover": 1.0,
    "kiting": 1.0,
    "dormant": 1.0,
    "anomaly": 1.0,
}

_TRIGGER_THRESHOLD: float = 0.5

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_scores(scores: pd.Series) -> pd.Series:
    """Min-max normalize a Series of scores to the [0, 1] range.

    If all values are identical (zero variance), returns a Series of zeros.
    """
    smin = scores.min()
    smax = scores.max()
    if smax == smin:
        return pd.Series(0.0, index=scores.index, name=scores.name)
    return (scores - smin) / (smax - smin)


def _assign_tier(score: float) -> str:
    """Map a composite score to a risk tier string."""
    if score >= TIER_THRESHOLDS["HIGH"]:
        return "CRITICAL"
    if score >= TIER_THRESHOLDS["MEDIUM"]:
        return "HIGH"
    if score >= TIER_THRESHOLDS["LOW"]:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------


def compute_composite_score(
    detector_results: dict[str, pd.DataFrame],
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Combine per-detector risk scores into a single composite score.

    Args:
        detector_results: Mapping of detector name to a DataFrame that must
            contain at least ``account_id`` and ``risk_score`` columns.
        weights: Optional mapping of detector name to numeric weight.  If
            ``None``, all detectors are weighted equally (weight = 1.0).

    Returns:
        DataFrame with columns:
            * ``account_id``
            * ``composite_score`` -- weighted average of normalized scores
            * ``risk_tier`` -- one of LOW / MEDIUM / HIGH / CRITICAL
            * ``triggered_detectors`` -- list of detector names whose
              normalized score exceeded the trigger threshold (0.5)
    """
    if not detector_results:
        logger.warning("No detector results provided; returning empty DataFrame")
        return pd.DataFrame(
            columns=["account_id", "composite_score", "risk_tier", "triggered_detectors"]
        )

    if weights is None:
        weights = {name: 1.0 for name in detector_results}

    # Normalize and collect each detector's scores
    normalized: dict[str, pd.Series] = {}
    frames: list[pd.DataFrame] = []

    for name, result_df in detector_results.items():
        if "account_id" not in result_df.columns or "risk_score" not in result_df.columns:
            logger.warning(
                "Detector '%s' missing required columns (account_id, risk_score) -- skipping",
                name,
            )
            continue

        score_series = normalize_scores(result_df["risk_score"])
        tmp = result_df[["account_id"]].copy()
        tmp[f"score_{name}"] = score_series.values
        frames.append(tmp)
        normalized[name] = score_series

    if not frames:
        logger.warning("No valid detector results after validation")
        return pd.DataFrame(
            columns=["account_id", "composite_score", "risk_tier", "triggered_detectors"]
        )

    # Merge all normalized scores on account_id
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="account_id", how="outer")

    score_cols = [c for c in merged.columns if c.startswith("score_")]

    # Compute weighted average (missing scores treated as 0)
    merged[score_cols] = merged[score_cols].fillna(0.0)

    total_weight = sum(weights.get(name, 1.0) for name in normalized)
    if total_weight == 0:
        total_weight = 1.0  # guard against division by zero

    merged["composite_score"] = sum(
        merged[f"score_{name}"] * weights.get(name, 1.0)
        for name in normalized
    ) / total_weight

    # Assign risk tier
    merged["risk_tier"] = merged["composite_score"].apply(_assign_tier)

    # Identify triggered detectors per account
    def _triggered(row: pd.Series) -> list[str]:
        return [
            name
            for name in normalized
            if row.get(f"score_{name}", 0.0) > _TRIGGER_THRESHOLD
        ]

    merged["triggered_detectors"] = merged.apply(_triggered, axis=1)

    result = merged[["account_id", "composite_score", "risk_tier", "triggered_detectors"]].copy()
    result = result.sort_values("composite_score", ascending=False).reset_index(drop=True)

    logger.info(
        "Composite scores computed for %d accounts — tiers: %s",
        len(result),
        result["risk_tier"].value_counts().to_dict(),
    )
    return result
