"""Account takeover detector — flag brute force, credential stuffing, and suspicious login patterns."""

from __future__ import annotations

import pandas as pd


def detect(
    login_attempts: pd.DataFrame,
    login_results: pd.DataFrame | None = None,
    user_edits: pd.DataFrame | None = None,
) -> list[dict]:
    """Run ATO rules against login_attempts_fct DataFrame.

    Columns used: username, result_id, attempted_at, client_ip
    """
    alerts: list[dict] = []
    if login_attempts.empty:
        return alerts

    df = login_attempts.copy()
    df["attempted_at"] = pd.to_datetime(df["attempted_at"])

    # Build success/failure per username
    user_stats = df.groupby("username").agg(
        total_attempts=("result_id", "size"),
        failed=("result_id", lambda x: (x != 1).sum()),
        succeeded=("result_id", lambda x: (x == 1).sum()),
        distinct_ips=("client_ip", "nunique"),
        first_attempt=("attempted_at", "min"),
        last_attempt=("attempted_at", "max"),
    ).reset_index()
    user_stats["failure_rate"] = user_stats["failed"] / user_stats["total_attempts"]

    # ------------------------------------------------------------------
    # Rule 1: High failure rate (> 50%) with meaningful attempt count
    # ------------------------------------------------------------------
    brute = user_stats[(user_stats["failure_rate"] > 0.5) & (user_stats["failed"] >= 5)]
    for _, row in brute.iterrows():
        severity = "CRITICAL" if row["failed"] >= 10 else "HIGH"
        score = 40 if severity == "CRITICAL" else 25
        alerts.append({
            "account_id": "",
            "user_id": row["username"],
            "member_number": "",
            "fraud_type": "account_takeover",
            "severity": severity,
            "score": score,
            "evidence": (
                f"Brute force: {row['failed']}/{row['total_attempts']} failed attempts "
                f"({row['failure_rate']:.0%} failure rate), {row['distinct_ips']} distinct IPs"
            ),
        })

    # ------------------------------------------------------------------
    # Rule 2: Rapid-fire failures (> 5 failures within 5 minutes)
    # ------------------------------------------------------------------
    failed_df = df[df["result_id"] != 1].sort_values(["username", "attempted_at"])
    for username, grp in failed_df.groupby("username"):
        if len(grp) < 5:
            continue
        times = grp["attempted_at"].values
        for i in range(len(times) - 4):
            window = times[i + 4] - times[i]
            if window <= pd.Timedelta(minutes=5):
                # already flagged by rule 1? add extra evidence
                existing = [a for a in alerts if a["user_id"] == username]
                if existing:
                    existing[0]["evidence"] += f" | Rapid burst: 5+ failures in 5 min"
                    if existing[0]["severity"] != "CRITICAL":
                        existing[0]["severity"] = "CRITICAL"
                        existing[0]["score"] = 40
                else:
                    alerts.append({
                        "account_id": "",
                        "user_id": username,
                        "member_number": "",
                        "fraud_type": "account_takeover",
                        "severity": "CRITICAL",
                        "score": 40,
                        "evidence": (
                            f"Rapid-fire failures: 5+ failures within 5 minutes for {username}"
                        ),
                    })
                break

    # ------------------------------------------------------------------
    # Rule 3: IP velocity — > 3 distinct IPs in 7 days
    # ------------------------------------------------------------------
    high_ip = user_stats[user_stats["distinct_ips"] > 3]
    for _, row in high_ip.iterrows():
        # skip if already flagged
        if any(a["user_id"] == row["username"] for a in alerts):
            # append IP info to existing alert
            for a in alerts:
                if a["user_id"] == row["username"]:
                    if f"{row['distinct_ips']} distinct IPs" not in a["evidence"]:
                        a["evidence"] += f" | IP velocity: {row['distinct_ips']} distinct IPs"
            continue
        severity = "HIGH" if row["distinct_ips"] >= 5 else "MEDIUM"
        score = 25 if severity == "HIGH" else 10
        alerts.append({
            "account_id": "",
            "user_id": row["username"],
            "member_number": "",
            "fraud_type": "account_takeover",
            "severity": severity,
            "score": score,
            "evidence": (
                f"IP velocity: {row['distinct_ips']} distinct IPs, "
                f"{row['total_attempts']} total attempts, "
                f"{row['failure_rate']:.0%} failure rate"
            ),
        })

    # ------------------------------------------------------------------
    # Rule 4: All-fail users (100% failure, >= 3 attempts)
    # ------------------------------------------------------------------
    all_fail = user_stats[
        (user_stats["failure_rate"] == 1.0) & (user_stats["total_attempts"] >= 3)
    ]
    for _, row in all_fail.iterrows():
        if any(a["user_id"] == row["username"] for a in alerts):
            continue
        alerts.append({
            "account_id": "",
            "user_id": row["username"],
            "member_number": "",
            "fraud_type": "account_takeover",
            "severity": "HIGH",
            "score": 25,
            "evidence": (
                f"100% failure rate: {row['total_attempts']} attempts, all failed, "
                f"{row['distinct_ips']} distinct IPs"
            ),
        })

    return alerts
