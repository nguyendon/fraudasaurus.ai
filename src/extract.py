"""Extract BigQuery tables to local parquet files.

Usage:
    python -m src.extract              # extract all tables
    python -m src.extract --dataset banno_operation_and_transaction_data
    python -m src.extract --table banno_operation_and_transaction_data.transactions_fct
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT = "jhdevcon2026"
OUTPUT_DIR = Path("data/raw")

DATASETS = [
    "banno_operation_and_transaction_data",
    "ip_geo",
    "symitar",
]


def get_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT)


def list_tables(client: bigquery.Client, dataset: str) -> list[str]:
    tables = client.list_tables(f"{PROJECT}.{dataset}")
    return [t.table_id for t in tables]


def extract_table(client: bigquery.Client, dataset: str, table: str, output_dir: Path) -> Path:
    dest = output_dir / dataset
    dest.mkdir(parents=True, exist_ok=True)
    out_path = dest / f"{table}.parquet"

    if out_path.exists():
        logger.info("SKIP %s.%s (already exists)", dataset, table)
        return out_path

    logger.info("Extracting %s.%s ...", dataset, table)
    query = f"SELECT * FROM `{PROJECT}.{dataset}.{table}`"
    df = client.query(query).to_dataframe()
    df.to_parquet(out_path, index=False)
    logger.info("  -> %s (%d rows, %.1f MB)", out_path, len(df), out_path.stat().st_size / 1e6)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Extract BigQuery tables to parquet")
    parser.add_argument("--dataset", help="Extract only this dataset")
    parser.add_argument("--table", help="Extract a single table (format: dataset.table)")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    client = get_client()

    if args.table:
        dataset, table = args.table.split(".", 1)
        extract_table(client, dataset, table, output_dir)
        return

    datasets = [args.dataset] if args.dataset else DATASETS
    for dataset in datasets:
        tables = list_tables(client, dataset)
        logger.info("Dataset %s: %d tables", dataset, len(tables))
        for table in tables:
            try:
                extract_table(client, dataset, table, output_dir)
            except Exception:
                logger.exception("FAILED %s.%s", dataset, table)


if __name__ == "__main__":
    main()
