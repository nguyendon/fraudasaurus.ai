"""Unsupervised anomaly detector for Fraudasaurus.ai.

Uses scikit-learn's ``IsolationForest`` to identify statistical outliers
in a per-account feature matrix.  No labeled fraud data is required --
the algorithm isolates anomalies by exploiting the fact that unusual
observations are easier to separate via random partitioning.

The detector can consume a pre-built feature matrix from
``src.features.build_feature_matrix`` or build one inline from raw
transactions when the features module has not been run.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
except ImportError:  # pragma: no cover
    IsolationForest = None  # type: ignore[misc,assignment]
    StandardScaler = None  # type: ignore[misc,assignment]
    logging.getLogger(__name__).warning(
        "scikit-learn is not installed; AnomalyDetector will return empty results"
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column aliases (used only when building features inline)
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


# ---------------------------------------------------------------------------
# Inline feature builder (fallback when src.features is unavailable)
# ---------------------------------------------------------------------------


def _build_features_inline(df: pd.DataFrame) -> pd.DataFrame:
    """Build a minimal per-account feature matrix from raw transactions.

    This is a simplified version of ``src.features.build_feature_matrix``
    designed as a fallback.  It computes:

    * ``txn_count`` -- total transactions per account
    * ``amount_mean`` / ``amount_std`` / ``amount_max``
    * ``days_active`` -- distinct transaction dates
    * ``weekend_fraction`` -- share of weekend transactions
    * ``late_night_fraction`` -- share of transactions 22:00--06:00
    * ``unique_channels`` -- number of distinct channels (if available)
    * ``deposit_withdrawal_ratio`` -- total deposits / total withdrawals
    """
    acct_col = _resolve_column(df, "account_id")
    date_col = _resolve_column(df, "transaction_date")
    amt_col = _resolve_column(df, "amount")

    if acct_col is None or date_col is None or amt_col is None:
        raise ValueError(
            "Cannot build features inline: missing account_id, "
            "transaction_date, or amount columns"
        )

    work = df.copy()
    work[date_col] = _ensure_datetime(work[date_col])
    work[amt_col] = pd.to_numeric(work[amt_col], errors="coerce")
    work = work.dropna(subset=[acct_col, date_col, amt_col])

    # Basic aggregations
    agg = (
        work.groupby(acct_col)
        .agg(
            txn_count=(amt_col, "count"),
            amount_mean=(amt_col, "mean"),
            amount_std=(amt_col, "std"),
            amount_max=(amt_col, "max"),
        )
        .reset_index()
    )
    agg["amount_std"] = agg["amount_std"].fillna(0.0)
    agg = agg.rename(columns={acct_col: "account_id"})

    # Days active
    days_active = (
        work.groupby(acct_col)[date_col]
        .apply(lambda s: s.dt.normalize().nunique())
        .rename("days_active")
        .reset_index()
        .rename(columns={acct_col: "account_id"})
    )
    agg = agg.merge(days_active, on="account_id", how="left")

    # Weekend & late-night fractions
    work["_dow"] = work[date_col].dt.dayofweek
    work["_hour"] = work[date_col].dt.hour

    time_feats = (
        work.groupby(acct_col)
        .agg(
            weekend_fraction=("_dow", lambda x: (x >= 5).mean()),
            late_night_fraction=(
                "_hour",
                lambda x: ((x >= 22) | (x < 6)).mean(),
            ),
        )
        .reset_index()
        .rename(columns={acct_col: "account_id"})
    )
    agg = agg.merge(time_feats, on="account_id", how="left")

    # Channel diversity
    chan_col = _resolve_column(df, "channel")
    if chan_col is not None:
        chan_div = (
            work.groupby(acct_col)[chan_col]
            .nunique()
            .rename("unique_channels")
            .reset_index()
            .rename(columns={acct_col: "account_id"})
        )
        agg = agg.merge(chan_div, on="account_id", how="left")

    # Deposit / withdrawal ratio
    type_col = _resolve_column(df, "transaction_type")
    if type_col is not None:
        normed_type = work[type_col].str.strip().str.lower()
        dep_mask = normed_type.isin(["deposit", "dep", "credit", "cr"])
        wd_mask = normed_type.isin(
            ["withdrawal", "wd", "debit", "dr", "withdraw"]
        )

        dep_total = (
            work[dep_mask].groupby(acct_col)[amt_col].sum().rename("_dep")
        )
        wd_total = (
            work[wd_mask].groupby(acct_col)[amt_col].sum().rename("_wd")
        )
        dw = pd.concat([dep_total, wd_total], axis=1).fillna(0.0)
        dw["deposit_withdrawal_ratio"] = dw["_dep"] / dw["_wd"].replace(
            0, float("nan")
        )
        dw["deposit_withdrawal_ratio"] = dw["deposit_withdrawal_ratio"].fillna(0.0)
        dw = (
            dw[["deposit_withdrawal_ratio"]]
            .reset_index()
            .rename(columns={acct_col: "account_id"})
        )
        agg = agg.merge(dw, on="account_id", how="left")

    agg = agg.set_index("account_id").sort_index()
    agg = agg.fillna(0.0)

    logger.info(
        "Built inline feature matrix: %d accounts x %d features",
        agg.shape[0],
        agg.shape[1],
    )
    return agg


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class AnomalyDetector:
    """Unsupervised anomaly detector using Isolation Forest.

    Parameters
    ----------
    contamination : float
        Expected proportion of anomalies in the dataset (default 0.05).
    n_estimators : int
        Number of isolation trees (default 200).
    random_state : int
        Random seed for reproducibility (default 42).
    use_features_module : bool
        If ``True`` (default), try to import and use
        ``src.features.build_feature_matrix``.  If that fails, fall
        back to the inline feature builder.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 200,
        random_state: int = 42,
        use_features_module: bool = True,
    ) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.use_features_module = use_features_module

        # Fitted model state
        self._model: Optional[object] = None
        self._scaler: Optional[object] = None
        self._feature_columns: Optional[List[str]] = None

    # ---- public API -------------------------------------------------------

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run anomaly detection on a transactions DataFrame.

        Builds a feature matrix (via ``src.features`` or inline), fits
        an Isolation Forest, and returns per-account anomaly scores
        normalised to [0, 1].

        Parameters
        ----------
        df : pd.DataFrame
            Raw transactions or a pre-built feature matrix.  If the
            DataFrame is indexed by ``account_id`` and contains only
            numeric columns, it is treated as a pre-built matrix.

        Returns
        -------
        pd.DataFrame
            Columns: ``account_id``, ``risk_score`` (0--1), ``flags``.
        """
        if IsolationForest is None:
            logger.error(
                "scikit-learn is required for AnomalyDetector but is not "
                "installed"
            )
            return self._empty_result()

        if df.empty:
            logger.warning("Empty DataFrame passed to AnomalyDetector")
            return self._empty_result()

        feature_matrix = self._get_feature_matrix(df)

        if feature_matrix.empty:
            logger.warning("Feature matrix is empty; returning empty results")
            return self._empty_result()

        return self._fit_and_score(feature_matrix)

    def fit_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convenience method: equivalent to ``detect(df)``.

        This alias exists for API consistency with scikit-learn
        conventions.
        """
        return self.detect(df)

    # ---- internal ---------------------------------------------------------

    def _get_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Obtain a per-account feature matrix.

        Strategy:
        1. If ``df`` looks like a pre-built feature matrix (indexed by
           ``account_id``, all numeric columns), use it directly.
        2. Try ``src.features.build_feature_matrix``.
        3. Fall back to ``_build_features_inline``.
        """
        # Check if already a feature matrix
        if self._looks_like_feature_matrix(df):
            logger.info("Input appears to be a pre-built feature matrix")
            return df.copy()

        # Try the features module
        if self.use_features_module:
            try:
                from src.features import build_feature_matrix  # type: ignore[import-untyped]

                logger.info("Using src.features.build_feature_matrix")
                return build_feature_matrix(df)
            except (ImportError, Exception) as exc:
                logger.info(
                    "Could not use src.features (%s); falling back to "
                    "inline feature builder",
                    exc,
                )

        # Inline fallback
        try:
            return _build_features_inline(df)
        except Exception as exc:
            logger.error("Failed to build features inline: %s", exc)
            return pd.DataFrame()

    @staticmethod
    def _looks_like_feature_matrix(df: pd.DataFrame) -> bool:
        """Heuristic: is this DF already a per-account feature matrix?"""
        if df.index.name == "account_id":
            numeric_cols = df.select_dtypes(include="number").columns
            return len(numeric_cols) == len(df.columns) and len(df.columns) >= 3
        return False

    def _fit_and_score(
        self, feature_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """Fit IsolationForest and return normalised anomaly scores."""
        # Ensure all-numeric, drop any remaining non-numeric columns
        numeric_matrix = feature_matrix.select_dtypes(include="number").copy()
        numeric_matrix = numeric_matrix.replace([np.inf, -np.inf], np.nan)
        numeric_matrix = numeric_matrix.fillna(0.0)

        if numeric_matrix.empty or numeric_matrix.shape[1] == 0:
            logger.warning("No numeric features available for anomaly detection")
            return self._empty_result()

        self._feature_columns = list(numeric_matrix.columns)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(numeric_matrix.values)
        self._scaler = scaler

        # Fit Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )
        model.fit(X_scaled)
        self._model = model

        # Raw anomaly scores: lower (more negative) = more anomalous
        raw_scores = model.decision_function(X_scaled)

        # Normalise to [0, 1] where 1 = most anomalous
        # decision_function returns negative values for anomalies
        # We invert so that higher = more suspicious
        score_min = raw_scores.min()
        score_max = raw_scores.max()
        if score_max == score_min:
            normalised = np.zeros(len(raw_scores))
        else:
            normalised = (score_max - raw_scores) / (score_max - score_min)

        normalised = np.clip(normalised, 0.0, 1.0)

        # Build result
        account_ids = feature_matrix.index.tolist()
        predictions = model.predict(X_scaled)  # -1 = anomaly, 1 = normal

        records: List[Dict] = []
        for i, acct in enumerate(account_ids):
            risk_score = float(normalised[i])
            flags: List[str] = []

            if predictions[i] == -1:
                # Identify the top contributing features
                top_features = self._get_top_features(
                    numeric_matrix.iloc[i], X_scaled[i]
                )
                flags.append(
                    f"Statistical anomaly detected (score={risk_score:.3f})"
                )
                if top_features:
                    flags.append(
                        f"Top anomalous features: {', '.join(top_features)}"
                    )

            if risk_score > 0 and flags:
                records.append({
                    "account_id": acct,
                    "risk_score": risk_score,
                    "flags": flags,
                })

        if not records:
            logger.info("AnomalyDetector: no anomalies detected")
            return self._empty_result()

        result = (
            pd.DataFrame(records)
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True)
        )

        logger.info(
            "AnomalyDetector flagged %d / %d accounts (contamination=%.2f)",
            len(result),
            len(account_ids),
            self.contamination,
        )
        return result

    def _get_top_features(
        self,
        raw_row: pd.Series,
        scaled_row: np.ndarray,
        top_n: int = 3,
    ) -> List[str]:
        """Identify the features with the largest absolute scaled values.

        These are the features that deviate most from the population
        mean (after standardization) and likely contribute most to the
        anomaly score.
        """
        if self._feature_columns is None:
            return []

        abs_scaled = np.abs(scaled_row)
        top_indices = np.argsort(abs_scaled)[::-1][:top_n]

        result: List[str] = []
        for idx in top_indices:
            if idx < len(self._feature_columns):
                feat_name = self._feature_columns[idx]
                feat_val = raw_row.iloc[idx] if idx < len(raw_row) else "?"
                direction = "high" if scaled_row[idx] > 0 else "low"
                result.append(f"{feat_name}={feat_val:.2f} ({direction})")

        return result

    @staticmethod
    def _empty_result() -> pd.DataFrame:
        """Return an empty result DataFrame with the correct schema."""
        return pd.DataFrame(
            columns=["account_id", "risk_score", "flags"]
        ).astype({"risk_score": float})
