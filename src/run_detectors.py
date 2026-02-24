"""Orchestrator — load data from BigQuery, run all fraud detectors, score, and output results."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src import bq_loader
from src.detectors import structuring, account_takeover, dormant, multi_identity
from src.scoring import score_alerts

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load data from BigQuery
    # ------------------------------------------------------------------
    logger.info("Loading data from BigQuery ...")

    logger.info("  transactions_fct ...")
    transactions = bq_loader.load_transactions()
    logger.info("    %d rows", len(transactions))

    logger.info("  login_attempts_fct ...")
    login_attempts = bq_loader.load_login_attempts()
    logger.info("    %d rows", len(login_attempts))

    logger.info("  users_fct ...")
    users = bq_loader.load_users()
    logger.info("    %d rows", len(users))

    logger.info("  user_member_number_associations_fct ...")
    user_member_assoc = bq_loader.load_user_member_associations()
    logger.info("    %d rows", len(user_member_assoc))

    logger.info("  symitar.account_v1_raw ...")
    symitar_accounts = bq_loader.load_symitar_accounts()
    logger.info("    %d rows", len(symitar_accounts))

    logger.info("  user_edits_fct ...")
    user_edits = bq_loader.load_user_edits()
    logger.info("    %d rows", len(user_edits))

    # ------------------------------------------------------------------
    # Run detectors
    # ------------------------------------------------------------------
    all_alerts: list[dict] = []

    logger.info("Running structuring detector ...")
    alerts = structuring.detect(transactions)
    logger.info("  %d alerts", len(alerts))
    all_alerts.extend(alerts)

    logger.info("Running account takeover detector ...")
    alerts = account_takeover.detect(login_attempts, user_edits=user_edits)
    logger.info("  %d alerts", len(alerts))
    all_alerts.extend(alerts)

    logger.info("Running dormant account detector ...")
    alerts = dormant.detect(symitar_accounts, transactions, user_member_assoc)
    logger.info("  %d alerts", len(alerts))
    all_alerts.extend(alerts)

    logger.info("Running multi-identity detector ...")
    alerts = multi_identity.detect(users, login_attempts, user_member_assoc)
    logger.info("  %d alerts", len(alerts))
    all_alerts.extend(alerts)

    # ------------------------------------------------------------------
    # Score and output
    # ------------------------------------------------------------------
    logger.info("Scoring %d total alerts ...", len(all_alerts))
    results = score_alerts(all_alerts)

    out_path = OUTPUT_DIR / "fraud_alerts.csv"
    results.to_csv(out_path, index=False)
    logger.info("Saved %d scored accounts to %s", len(results), out_path)

    # Also save raw alerts (pre-scoring) for debugging
    raw_path = OUTPUT_DIR / "fraud_alerts_raw.csv"
    pd.DataFrame(all_alerts).to_csv(raw_path, index=False)
    logger.info("Saved %d raw alerts to %s", len(all_alerts), raw_path)

    # Print summary
    print("\n" + "=" * 70)
    print("FRAUD DETECTION RESULTS")
    print("=" * 70)
    print(f"\nTotal alerts: {len(all_alerts)}")
    print(f"Unique accounts/users flagged: {len(results)}")
    print(f"\nOutputs:")
    print(f"  {out_path}   (scored, one row per account)")
    print(f"  {raw_path}  (raw alerts, one row per rule hit)")

    if not results.empty:
        print(f"\nTier distribution:")
        for tier in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = (results["tier"] == tier).sum()
            if count:
                print(f"  {tier}: {count}")

        print(f"\nTop 15 highest risk:")
        print("-" * 90)
        top = results.head(15)
        for _, row in top.iterrows():
            label = row["user_id"] or row["account_id"] or row["member_number"]
            print(f"\n  [{row['tier']:8s}] Score {row['composite_score']:3.0f} | {label}")
            print(f"  Types: {row['fraud_types']}")
            # Show each evidence item on its own line, no truncation
            for piece in row["evidence_summary"].split(" | "):
                print(f"    - {piece}")


if __name__ == "__main__":
    main()
