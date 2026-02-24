"""
bq_loader.py — Query Google BigQuery and return pandas DataFrames.

Results are cached to data/raw/ as parquet files. Delete the cache dir to re-fetch.

Project: jhdevcon2026
"""

import logging
from pathlib import Path

from google.cloud import bigquery
import pandas as pd

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/raw")


# ---------------------------------------------------------------------------
# Cache helper
# ---------------------------------------------------------------------------

def _cached_query(name: str, sql: str) -> pd.DataFrame:
    """Return cached parquet if it exists, otherwise query BigQuery and cache."""
    cache_path = CACHE_DIR / f"{name}.parquet"
    if cache_path.exists():
        logger.info("  (cached) %s", cache_path)
        return pd.read_parquet(cache_path)

    logger.info("  (querying BigQuery) %s ...", name)
    client = get_client()
    df = client.query(sql).to_dataframe(progress_bar_type="tqdm")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False)
    logger.info("  cached to %s (%d rows)", cache_path, len(df))
    return df


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def get_client() -> bigquery.Client:
    """Return a BigQuery client for the jhdevcon2026 project."""
    return bigquery.Client(project="jhdevcon2026")


# ---------------------------------------------------------------------------
# Banno tables
# ---------------------------------------------------------------------------

def load_transactions() -> pd.DataFrame:
    """Load transactions_fct (only columns needed by detectors)."""
    return _cached_query("transactions_fct", """
        SELECT AccountId, DatePosted, Amount, BannoType, UserId, Memo, CleanMemo
        FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
    """)


def load_login_attempts() -> pd.DataFrame:
    """Load login_attempts_fct (only columns needed by detectors)."""
    return _cached_query("login_attempts_fct", """
        SELECT username, result_id, attempted_at, client_ip
        FROM `jhdevcon2026.banno_operation_and_transaction_data.login_attempts_fct`
    """)


def load_users() -> pd.DataFrame:
    """Load all rows from users_fct."""
    return _cached_query("users_fct",
        "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.users_fct`")


def load_user_member_associations() -> pd.DataFrame:
    """Load all rows from user_member_number_associations_fct."""
    return _cached_query("user_member_number_associations_fct",
        "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct`")


def load_scheduled_transfers() -> pd.DataFrame:
    """Load all rows from scheduled_transfers_fct."""
    return _cached_query("scheduled_transfers_fct",
        "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.scheduled_transfers_fct`")


def load_rdc_deposits() -> pd.DataFrame:
    """Load all rows from rdc_deposits_fct (remote deposit capture)."""
    return _cached_query("rdc_deposits_fct",
        "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.rdc_deposits_fct`")


def load_user_edits() -> pd.DataFrame:
    """Load all rows from user_edits_fct."""
    return _cached_query("user_edits_fct",
        "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.user_edits_fct`")


def load_login_results() -> pd.DataFrame:
    """Load all rows from login_results_deref."""
    return _cached_query("login_results_deref",
        "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.login_results_deref`")


# ---------------------------------------------------------------------------
# Symitar tables
# ---------------------------------------------------------------------------

def load_symitar_accounts() -> pd.DataFrame:
    """Load symitar account_v1_raw (only columns needed by detectors)."""
    return _cached_query("symitar_account_v1_raw", """
        SELECT number, lastfmdate, memberstatus, opendate
        FROM `jhdevcon2026.symitar.account_v1_raw`
    """)


# ---------------------------------------------------------------------------
# Ad-hoc query (not cached)
# ---------------------------------------------------------------------------

def run_query(sql: str) -> pd.DataFrame:
    """Run an arbitrary SQL string and return the result as a DataFrame."""
    client = get_client()
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


# ---------------------------------------------------------------------------
# Connection test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Testing BigQuery connection to jhdevcon2026 ...")
    client = get_client()
    row_counts = client.query(
        """
        SELECT 'transactions_fct' AS table_name,
               COUNT(*) AS row_count
        FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
        """
    ).to_dataframe()
    print(row_counts.to_string(index=False))
    print("Connection OK.")
