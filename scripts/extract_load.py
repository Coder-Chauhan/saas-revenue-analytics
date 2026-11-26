"""Extract-Load step: land every source system into the `raw` schema of the warehouse.

ELT pattern: this script only extracts and loads (with light schema checks and load
metadata). All business transformation happens later in dbt.

  CRM CSV export        -> raw.crm_accounts
  Billing API (JSON)    -> raw.billing_subscriptions, raw.billing_invoices  (pages flattened)
  Product events CSV    -> raw.product_events, raw.product_features

Each load is recorded in raw._load_audit (source, rows, columns, status, timestamp) so
loads can be monitored over time.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "warehouse.duckdb"

EXPECTED = {
    "crm_accounts": {"account_id", "account_name", "industry", "segment", "region", "country",
                     "account_owner", "created_date"},
    "billing_subscriptions": {"subscription_id", "account_id", "plan", "start_date", "end_date",
                              "status", "billing_interval"},
    "billing_invoices": {"invoice_id", "subscription_id", "account_id", "invoice_date", "period_start",
                         "seats", "amount", "currency", "status"},
    "product_events": {"event_id", "account_id", "user_id", "event_timestamp", "event_type", "feature_id"},
    "product_features": {"feature_id", "feature_name", "feature_area"},
}


def read_paginated_json(path: Path) -> pd.DataFrame:
    """Flatten a paginated API dump ([{page, total_pages, data: [...]}, ...]) into one frame."""
    pages = json.loads(path.read_text())
    expected_pages = pages[0]["total_pages"] if pages else 0
    if len(pages) != expected_pages:
        raise ValueError(f"{path.name}: expected {expected_pages} pages, got {len(pages)}")
    return pd.DataFrame([row for page in pages for row in page["data"]])


def extract() -> dict[str, tuple[pd.DataFrame, str]]:
    return {
        "crm_accounts": (pd.read_csv(RAW / "crm_accounts.csv", dtype=str, keep_default_na=False), "crm_accounts.csv"),
        "billing_subscriptions": (read_paginated_json(RAW / "billing_subscriptions.json"), "billing_subscriptions.json"),
        "billing_invoices": (read_paginated_json(RAW / "billing_invoices.json"), "billing_invoices.json"),
        "product_events": (pd.read_csv(RAW / "product_events.csv", dtype=str), "product_events.csv"),
        "product_features": (pd.read_csv(RAW / "product_features.csv", dtype=str), "product_features.csv"),
    }


def main() -> int:
    con = duckdb.connect(str(DB))
    con.execute("create schema if not exists raw")
    con.execute("""
        create table if not exists raw._load_audit (
            table_name varchar, source_file varchar, row_count integer, column_count integer,
            status varchar, message varchar, loaded_at timestamp)
    """)
    failures = 0
    loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)
    for table, (df, source) in extract().items():
        missing = EXPECTED[table] - set(df.columns)
        if missing:
            failures += 1
            con.execute("insert into raw._load_audit values (?, ?, ?, ?, 'failed', ?, ?)",
                        [table, source, len(df), len(df.columns), f"missing columns: {sorted(missing)}", loaded_at])
            print(f"FAILED {table}: missing columns {sorted(missing)}")
            continue
        df = df.assign(_source_file=source, _loaded_at=loaded_at)
        con.register("df_view", df)
        con.execute(f"create or replace table raw.{table} as select * from df_view")
        con.unregister("df_view")
        con.execute("insert into raw._load_audit values (?, ?, ?, ?, 'success', null, ?)",
                    [table, source, len(df), len(df.columns) - 2, loaded_at])
        print(f"loaded raw.{table:<22} {len(df):>8,} rows")
    con.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
