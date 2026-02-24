"""Dormant account abuse detector — flag accounts dormant in core but active in digital banking."""

from __future__ import annotations

import pandas as pd
from datetime import date, timedelta


def detect(
    symitar_accounts: pd.DataFrame,
    transactions: pd.DataFrame,
    user_member_assoc: pd.DataFrame | None = None,
) -> list[dict]:
    """Run dormant-abuse rules by cross-referencing Symitar core accounts with Banno transactions.

    Symitar columns: number (account #), lastfmdate, memberstatus, opendate
    Transaction columns: AccountId, DatePosted, Amount, UserId
    Association columns: member_number, user_id, account_id (links Banno to Symitar)
    """
    alerts: list[dict] = []
    if symitar_accounts.empty or transactions.empty:
        return alerts

    today = date.today()
    one_year_ago = today - timedelta(days=365)
    five_years_ago = today - timedelta(days=5 * 365)

    # Prep Symitar accounts
    sym = symitar_accounts.copy()
    sym["lastfmdate"] = pd.to_datetime(sym["lastfmdate"]).dt.date
    # Pad account number to match member_number format if needed
    sym["number"] = sym["number"].astype(str).str.strip()

    # Find dormant accounts (no core activity in 12+ months)
    dormant = sym[sym["lastfmdate"] < one_year_ago].copy()
    if dormant.empty:
        return alerts

    # If we have user-member associations, use them to link Banno transactions to Symitar accounts
    if user_member_assoc is not None and not user_member_assoc.empty:
        assoc = user_member_assoc.copy()
        assoc["member_number"] = assoc["member_number"].astype(str).str.strip()

        # Join dormant Symitar accounts with Banno associations
        linked = dormant.merge(assoc, left_on="number", right_on="member_number", how="inner")

        if not linked.empty:
            # Get Banno transaction stats per linked account
            txn = transactions.copy()
            txn["DatePosted"] = pd.to_datetime(txn["DatePosted"])
            txn["AbsAmount"] = txn["Amount"].abs()

            for _, acct_row in linked.iterrows():
                member_num = acct_row["number"]
                banno_user_id = acct_row.get("user_id", "")

                # Find transactions for this user's accounts
                user_txns = txn[txn["UserId"] == banno_user_id]
                if user_txns.empty:
                    continue

                txn_count = len(user_txns)
                txn_total = user_txns["AbsAmount"].sum()
                last_txn = user_txns["DatePosted"].max().date()
                first_txn = user_txns["DatePosted"].min().date()

                dormancy_years = (today - acct_row["lastfmdate"]).days / 365.25

                # Rule 1: Dormant > 5 years + digital activity > $1k → CRITICAL
                if dormancy_years > 5 and txn_total > 1000:
                    alerts.append({
                        "account_id": str(user_txns["AccountId"].iloc[0]) if not user_txns.empty else "",
                        "user_id": str(banno_user_id),
                        "member_number": member_num,
                        "fraud_type": "dormant_abuse",
                        "severity": "CRITICAL",
                        "score": 40,
                        "evidence": (
                            f"Core dormant since {acct_row['lastfmdate']} ({dormancy_years:.1f} years) "
                            f"but {txn_count} digital transactions totaling ${txn_total:,.0f}, "
                            f"date range {first_txn} to {last_txn}"
                        ),
                    })
                # Rule 2: Dormant > 1 year + any digital activity → HIGH
                elif txn_count > 0:
                    alerts.append({
                        "account_id": str(user_txns["AccountId"].iloc[0]) if not user_txns.empty else "",
                        "user_id": str(banno_user_id),
                        "member_number": member_num,
                        "fraud_type": "dormant_abuse",
                        "severity": "HIGH",
                        "score": 25,
                        "evidence": (
                            f"Core dormant since {acct_row['lastfmdate']} ({dormancy_years:.1f} years) "
                            f"but {txn_count} digital transactions totaling ${txn_total:,.0f}"
                        ),
                    })
    else:
        # Fallback: no association table — look for member numbers in transaction memos
        # or just flag the dormant accounts with long inactivity
        very_dormant = dormant[dormant["lastfmdate"] < five_years_ago.date() if isinstance(five_years_ago, date) else five_years_ago]
        for _, row in very_dormant.head(20).iterrows():
            dormancy_years = (today - row["lastfmdate"]).days / 365.25
            alerts.append({
                "account_id": "",
                "user_id": "",
                "member_number": row["number"],
                "fraud_type": "dormant_abuse",
                "severity": "MEDIUM",
                "score": 10,
                "evidence": (
                    f"Core account dormant since {row['lastfmdate']} ({dormancy_years:.1f} years), "
                    f"member status: {row.get('memberstatus', 'unknown')}"
                ),
            })

    return alerts
