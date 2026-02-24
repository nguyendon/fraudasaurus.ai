"""
bq_loader.py — Query Google BigQuery and return pandas DataFrames.

Project: jhdevcon2026
Dataset: banno_operation_and_transaction_data, symitar
"""

from google.cloud import bigquery
import pandas as pd


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
    """Load all rows from transactions_fct."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_login_attempts() -> pd.DataFrame:
    """Load all rows from login_attempts_fct."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.login_attempts_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_users() -> pd.DataFrame:
    """Load all rows from users_fct."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.users_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_user_member_associations() -> pd.DataFrame:
    """Load all rows from user_member_number_associations_fct."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_scheduled_transfers() -> pd.DataFrame:
    """Load all rows from scheduled_transfers_fct."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.scheduled_transfers_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_rdc_deposits() -> pd.DataFrame:
    """Load all rows from rdc_deposits_fct (remote deposit capture)."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.rdc_deposits_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_user_edits() -> pd.DataFrame:
    """Load all rows from user_edits_fct."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.user_edits_fct`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


def load_login_results() -> pd.DataFrame:
    """Load all rows from login_results_deref."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.login_results_deref`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


# ---------------------------------------------------------------------------
# Symitar tables
# ---------------------------------------------------------------------------

def load_symitar_accounts() -> pd.DataFrame:
    """Load all rows from symitar account_v1_raw."""
    client = get_client()
    sql = "SELECT * FROM `jhdevcon2026.symitar.account_v1_raw`"
    return client.query(sql).to_dataframe(progress_bar_type="tqdm")


# ---------------------------------------------------------------------------
# Ad-hoc query
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
