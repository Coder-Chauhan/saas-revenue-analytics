# Data Quality Report

Generated 2026-11-26 18:33

## 1. Load health (latest run)

| Source table | Rows | Status |
|---|---:|---|
| billing_invoices | 5,865 | success |
| billing_subscriptions | 420 | success |
| crm_accounts | 421 | success |
| product_events | 109,757 | success |
| product_features | 10 | success |

## 2. Volume drift vs previous load

First load: no previous run to compare against.

## 3. Records quarantined by validation

| Source | Reason | Records |
|---|---|---:|
| billing_invoices | duplicate invoice_id | 1 |
| billing_invoices | invalid currency code: XXX | 1 |
| billing_invoices | negative amount | 1 |
| crm_accounts | duplicate account row | 1 |
| product_events | orphan event: unknown account ACC-9999 | 25 |

## 4. KPI anomalies (from Jan 2025)

| Month | MRR | Previous MRR | Logo churn |
|---|---:|---:|---:|
| Jan 2025 | $1,134,232 | $996,024 | 0.0% |
| May 2025 | $1,540,946 | $1,339,998 | 1.7% |

**Result: PASS** (0 failing checks)
