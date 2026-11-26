"""Data-quality monitoring report, run after every pipeline build.

Checks that catch issues before they reach dashboards:
  1. Load health      - every source loaded successfully in the latest run
  2. Volume drift     - row counts vs the previous load (flags swings above 20%)
  3. Rejected records - records quarantined by validation, grouped by reason
  4. KPI anomalies    - month-over-month MRR moves beyond 10%, and churn spikes
Writes docs/data_quality_report.md and exits non-zero if any check fails, so CI can block a bad build.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse.duckdb"
REPORT = ROOT / "docs" / "data_quality_report.md"
VOLUME_THRESHOLD = 0.20
MRR_THRESHOLD = 0.10


def main() -> int:
    con = duckdb.connect(str(DB), read_only=True)
    lines, failures = [f"# Data Quality Report\n\nGenerated {datetime.now():%Y-%m-%d %H:%M}\n"], 0

    # 1. Load health
    latest = con.sql("""
        select table_name, row_count, status, message
        from raw._load_audit
        where loaded_at = (select max(loaded_at) from raw._load_audit)
        order by table_name
    """).fetchall()
    lines.append("## 1. Load health (latest run)\n\n| Source table | Rows | Status |\n|---|---:|---|")
    for table, rows, status, message in latest:
        lines.append(f"| {table} | {rows:,} | {status}{' - ' + message if message else ''} |")
        failures += status != "success"

    # 2. Volume drift vs previous load
    drift = con.sql("""
        with ranked as (
            select table_name, row_count, loaded_at,
                   dense_rank() over (partition by table_name order by loaded_at desc) as rk
            from raw._load_audit where status = 'success'
        )
        select cur.table_name, prev.row_count, cur.row_count
        from ranked cur join ranked prev on cur.table_name = prev.table_name and cur.rk = 1 and prev.rk = 2
        order by cur.table_name
    """).fetchall()
    lines.append("\n## 2. Volume drift vs previous load\n")
    if not drift:
        lines.append("First load: no previous run to compare against.")
    else:
        lines.append("| Source table | Previous | Current | Change | Flag |\n|---|---:|---:|---:|---|")
        for table, prev, cur in drift:
            change = (cur - prev) / prev if prev else 0
            flag = "ALERT" if abs(change) > VOLUME_THRESHOLD else "ok"
            failures += flag == "ALERT"
            lines.append(f"| {table} | {prev:,} | {cur:,} | {change:+.1%} | {flag} |")

    # 3. Rejected records
    rejected = con.sql("""
        select source_table, reason, count(*) from quality.dq_rejected_records group by all order by 1, 3 desc
    """).fetchall()
    lines.append("\n## 3. Records quarantined by validation\n\n| Source | Reason | Records |\n|---|---|---:|")
    lines += [f"| {s} | {r} | {n:,} |" for s, r, n in rejected] or ["| - | none | 0 |"]

    # 4. KPI anomalies
    anomalies = con.sql(f"""
        with k as (
            select month_start, mrr_usd, logo_churn_rate,
                   lag(mrr_usd) over (order by month_start) as prev_mrr
            from finance.kpi_revenue_monthly
        )
        select month_start, mrr_usd, prev_mrr, logo_churn_rate
        from k
        where month_start >= date '2025-01-01'
          and (abs(mrr_usd - prev_mrr) / prev_mrr > {MRR_THRESHOLD} or logo_churn_rate > 0.05)
    """).fetchall()
    lines.append("\n## 4. KPI anomalies (from Jan 2025)\n")
    if anomalies:
        lines.append("| Month | MRR | Previous MRR | Logo churn |\n|---|---:|---:|---:|")
        lines += [f"| {m:%b %Y} | ${v:,.0f} | ${p:,.0f} | {c:.1%} |" for m, v, p, c in anomalies]
    else:
        lines.append(f"No month-over-month MRR change above {MRR_THRESHOLD:.0%} and no month with logo churn above 5%.")

    lines.append(f"\n**Result: {'FAIL' if failures else 'PASS'}** ({failures} failing checks)\n")
    REPORT.write_text("\n".join(lines))
    print(f"data quality: {'FAIL' if failures else 'PASS'} -> {REPORT.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
