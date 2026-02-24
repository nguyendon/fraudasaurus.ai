"""Multi-identity detector — flag one person operating multiple accounts under different names."""

from __future__ import annotations

import re
import pandas as pd


def _email_base(email: str) -> str:
    """Extract base username from email, ignoring domain and +aliases."""
    if not email or not isinstance(email, str):
        return ""
    local = email.split("@")[0].lower()
    local = re.sub(r"\+.*", "", local)  # strip +alias
    return local


def detect(
    users: pd.DataFrame,
    login_attempts: pd.DataFrame | None = None,
    user_member_assoc: pd.DataFrame | None = None,
) -> list[dict]:
    """Run multi-identity rules against users_fct DataFrame.

    User columns: user_id, primary_institution_username, first_name, last_name, email,
                  user_added_dt, user_active
    Login columns: username, client_ip, attempted_at
    """
    alerts: list[dict] = []
    if users.empty:
        return alerts

    df = users.copy()

    # ------------------------------------------------------------------
    # Rule 1: Email clustering — same email base, different names
    # ------------------------------------------------------------------
    df["email_base"] = df["email"].apply(_email_base)
    df["full_name"] = (
        df["first_name"].fillna("").str.strip() + " " + df["last_name"].fillna("").str.strip()
    ).str.strip().str.upper()

    # Group by email base (non-empty)
    email_groups = df[df["email_base"] != ""].groupby("email_base")
    for email_base, grp in email_groups:
        unique_names = grp["full_name"].nunique()
        num_accounts = len(grp)
        if num_accounts > 2 and unique_names > 1:
            names = ", ".join(grp["full_name"].unique()[:5])
            usernames = ", ".join(grp["primary_institution_username"].dropna().unique()[:5])
            severity = "CRITICAL" if num_accounts >= 5 else "HIGH"
            score = 40 if severity == "CRITICAL" else 25
            alerts.append({
                "account_id": "",
                "user_id": str(grp["user_id"].iloc[0]),
                "member_number": "",
                "fraud_type": "multi_identity",
                "severity": severity,
                "score": score,
                "evidence": (
                    f"Email base '{email_base}' linked to {num_accounts} accounts "
                    f"with {unique_names} different names: [{names}], "
                    f"usernames: [{usernames}]"
                ),
            })

    # ------------------------------------------------------------------
    # Rule 2: Same email domain variants (e.g., mbannister@jackhenry vs @symitar)
    # ------------------------------------------------------------------
    email_base_groups = df[df["email_base"] != ""].groupby("email_base")
    for email_base, grp in email_base_groups:
        domains = grp["email"].apply(lambda e: e.split("@")[1].lower() if "@" in str(e) else "").unique()
        domains = [d for d in domains if d]
        if len(domains) > 1 and len(grp) > 1:
            # already captured by rule 1? skip if so
            if any(a["evidence"].startswith(f"Email base '{email_base}'") for a in alerts):
                for a in alerts:
                    if a["evidence"].startswith(f"Email base '{email_base}'"):
                        a["evidence"] += f" | Multiple domains: [{', '.join(domains)}]"
                continue
            alerts.append({
                "account_id": "",
                "user_id": str(grp["user_id"].iloc[0]),
                "member_number": "",
                "fraud_type": "multi_identity",
                "severity": "HIGH",
                "score": 25,
                "evidence": (
                    f"Email base '{email_base}' uses multiple domains: "
                    f"[{', '.join(domains)}] across {len(grp)} accounts"
                ),
            })

    # ------------------------------------------------------------------
    # Rule 3: Account creation velocity — > 3 accounts from same email in 12 months
    # ------------------------------------------------------------------
    if "user_added_dt" in df.columns:
        df["added_date"] = pd.to_datetime(df["user_added_dt"])
        for email_base, grp in df[df["email_base"] != ""].groupby("email_base"):
            if len(grp) < 3:
                continue
            grp_sorted = grp.sort_values("added_date")
            dates = grp_sorted["added_date"].values
            for i in range(len(dates)):
                window_end = dates[i] + pd.Timedelta(days=365)
                window_count = ((dates >= dates[i]) & (dates <= window_end)).sum()
                if window_count >= 3:
                    # already flagged?
                    if any(a["evidence"].startswith(f"Email base '{email_base}'") for a in alerts):
                        for a in alerts:
                            if a["evidence"].startswith(f"Email base '{email_base}'"):
                                a["evidence"] += f" | {window_count} accounts created within 12 months"
                        break
                    alerts.append({
                        "account_id": "",
                        "user_id": str(grp_sorted["user_id"].iloc[0]),
                        "member_number": "",
                        "fraud_type": "multi_identity",
                        "severity": "HIGH",
                        "score": 25,
                        "evidence": (
                            f"Rapid account creation: {window_count} accounts with email base "
                            f"'{email_base}' created within 12 months"
                        ),
                    })
                    break

    # ------------------------------------------------------------------
    # Rule 4: Shared IP — multiple usernames from same IP within 30 min
    # ------------------------------------------------------------------
    if login_attempts is not None and not login_attempts.empty:
        logins = login_attempts.copy()
        logins["attempted_at"] = pd.to_datetime(logins["attempted_at"])
        logins = logins.sort_values("attempted_at")

        ip_user_groups = logins.groupby("client_ip").agg(
            usernames=("username", "nunique"),
            username_list=("username", lambda x: list(x.unique())),
        ).reset_index()

        shared_ip = ip_user_groups[ip_user_groups["usernames"] >= 3]
        for _, row in shared_ip.iterrows():
            # check for 30-min window overlap
            ip_logins = logins[logins["client_ip"] == row["client_ip"]]
            users_in_window = set()
            times = ip_logins[["username", "attempted_at"]].values
            for i in range(len(times)):
                window_users = {times[i][0]}
                for j in range(i + 1, len(times)):
                    if (times[j][1] - times[i][1]) <= pd.Timedelta(minutes=30):
                        window_users.add(times[j][0])
                    else:
                        break
                if len(window_users) >= 3:
                    users_in_window = window_users
                    break

            if len(users_in_window) >= 3:
                alerts.append({
                    "account_id": "",
                    "user_id": "",
                    "member_number": "",
                    "fraud_type": "multi_identity",
                    "severity": "HIGH",
                    "score": 25,
                    "evidence": (
                        f"Shared IP {row['client_ip']}: {len(users_in_window)} usernames "
                        f"within 30-min window: [{', '.join(list(users_in_window)[:5])}]"
                    ),
                })

    return alerts
