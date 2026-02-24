"""Structuring detector — flag sub-$10k transaction patterns designed to avoid CTR filing."""

from __future__ import annotations

import pandas as pd


def detect(transactions: pd.DataFrame) -> list[dict]:
    """Run structuring rules against transactions_fct DataFrame.

    Columns used: AccountId, DatePosted, Amount, BannoType, UserId, Memo, CleanMemo
    """
    alerts: list[dict] = []
    if transactions.empty:
        return alerts

    df = transactions.copy()
    df["AbsAmount"] = df["Amount"].abs()
    df["Date"] = pd.to_datetime(df["DatePosted"]).dt.date

    # ------------------------------------------------------------------
    # Rule 1: Exact $7,980 repeat pattern (strongest signal from findings)
    # ------------------------------------------------------------------
    mask_7980 = df["AbsAmount"] == 7980
    if mask_7980.any():
        grp = df[mask_7980].groupby("AccountId").agg(
            txn_count=("Amount", "size"),
            total_moved=("AbsAmount", "sum"),
            first_date=("Date", "min"),
            last_date=("Date", "max"),
            user_id=("UserId", "first"),
        )
        for acct_id, row in grp.iterrows():
            if row["txn_count"] >= 3:
                severity = "CRITICAL" if row["txn_count"] >= 10 else "HIGH"
                score = min(40 if severity == "CRITICAL" else 25, 40)
                alerts.append({
                    "account_id": acct_id,
                    "user_id": row["user_id"] if pd.notna(row["user_id"]) else "",
                    "member_number": "",
                    "fraud_type": "structuring",
                    "severity": severity,
                    "score": score,
                    "evidence": (
                        f"Exact $7,980 transactions: {row['txn_count']} times, "
                        f"${row['total_moved']:,.0f} total, "
                        f"{row['first_date']} to {row['last_date']}"
                    ),
                })

    # ------------------------------------------------------------------
    # Rule 2: Repeating amount detector — 3+ txns of same amount ($3k-$9,999) in 7-day window
    # ------------------------------------------------------------------
    cash_range = df[(df["AbsAmount"] >= 3000) & (df["AbsAmount"] <= 9999) & (df["AbsAmount"] != 7980)]
    if not cash_range.empty:
        cash_range = cash_range.copy()
        cash_range["DateParsed"] = pd.to_datetime(cash_range["Date"])
        for (acct_id, amount), grp in cash_range.groupby(["AccountId", "AbsAmount"]):
            grp_sorted = grp.sort_values("DateParsed")
            dates = grp_sorted["DateParsed"].values
            # sliding 7-day window
            for i in range(len(dates)):
                window_end = dates[i] + pd.Timedelta(days=7)
                window_count = ((dates >= dates[i]) & (dates <= window_end)).sum()
                if window_count >= 3:
                    total = amount * window_count
                    severity = "HIGH" if window_count >= 5 else "MEDIUM"
                    score = 25 if severity == "HIGH" else 10
                    alerts.append({
                        "account_id": acct_id,
                        "user_id": grp_sorted["UserId"].iloc[0] if pd.notna(grp_sorted["UserId"].iloc[0]) else "",
                        "member_number": "",
                        "fraud_type": "structuring",
                        "severity": severity,
                        "score": score,
                        "evidence": (
                            f"Repeating amount ${amount:,.0f}: {window_count} times in 7-day window, "
                            f"${total:,.0f} total"
                        ),
                    })
                    break  # one alert per account+amount combo

    # ------------------------------------------------------------------
    # Rule 3: Daily aggregation — daily sum > $10k but no single txn > $10k
    # ------------------------------------------------------------------
    daily = df.groupby(["AccountId", "Date"]).agg(
        daily_total=("AbsAmount", "sum"),
        max_single=("AbsAmount", "max"),
        txn_count=("Amount", "size"),
        user_id=("UserId", "first"),
    ).reset_index()

    suspicious_days = daily[(daily["daily_total"] > 10000) & (daily["max_single"] < 10000)]
    if not suspicious_days.empty:
        by_acct = suspicious_days.groupby("AccountId").agg(
            days_flagged=("Date", "size"),
            total_moved=("daily_total", "sum"),
            user_id=("user_id", "first"),
        )
        for acct_id, row in by_acct.iterrows():
            # skip if already flagged by rule 1
            if any(a["account_id"] == acct_id and a["evidence"].startswith("Exact $7,980") for a in alerts):
                continue
            severity = "CRITICAL" if row["days_flagged"] >= 5 else "HIGH"
            score = 40 if severity == "CRITICAL" else 25
            alerts.append({
                "account_id": acct_id,
                "user_id": row["user_id"] if pd.notna(row["user_id"]) else "",
                "member_number": "",
                "fraud_type": "structuring",
                "severity": severity,
                "score": score,
                "evidence": (
                    f"Daily sub-$10k structuring: {row['days_flagged']} days with daily total > $10k "
                    f"(no single txn > $10k), ${row['total_moved']:,.0f} total"
                ),
            })

    return alerts
