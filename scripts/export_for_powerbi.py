"""Export the star schema and KPI tables for Power BI.

Writes one CSV per table to exports/powerbi/. In Power BI Desktop: Get Data > Folder (or Text/CSV),
load every file, then follow docs/powerbi_guide.md for relationships and DAX measures.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports" / "powerbi"
TABLES = [
    "core.dim_date", "core.dim_customers", "core.dim_features",
    "finance.fct_invoices", "finance.fct_mrr_monthly", "finance.kpi_revenue_monthly",
    "product.fct_product_usage_daily", "product.kpi_product_monthly", "product.fct_feature_adoption_monthly",
    "quality.dq_rejected_records",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "warehouse.duckdb"), read_only=True)
    for t in TABLES:
        path = OUT / f"{t.split('.')[1]}.csv"
        con.sql(f"copy (select * from {t}) to '{path}' (header, delimiter ',')")
        n = con.sql(f"select count(*) from {t}").fetchall()[0][0]
        print(f"exported {t:<38} {n:>8,} rows -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
