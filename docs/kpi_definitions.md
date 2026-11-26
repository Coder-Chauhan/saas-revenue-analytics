# KPI Definitions

One documented definition per metric, so every dashboard and stakeholder uses the same numbers.
Each KPI lists its business meaning, exact calculation, source model and grain.

All revenue figures are in USD. "Month" means a calendar month (`month_start` = first day of the month).

## Revenue KPIs (`finance.kpi_revenue_monthly`)

| KPI | Definition | Calculation |
|---|---|---|
| **MRR** (Monthly Recurring Revenue) | Recurring subscription revenue billed for the month | Sum of `paid` and `open` invoice amounts for the period. `void` invoices are excluded |
| **ARR** (Annual Recurring Revenue) | MRR expressed annually | `MRR x 12` |
| **Starting MRR** | MRR at the end of the previous month | Sum of previous month MRR across accounts |
| **New MRR** | MRR from accounts paying for the first time | MRR of accounts with no prior paid month |
| **Expansion MRR** | Increase from existing paying accounts (more seats or a higher plan) | `MRR - previous MRR` where both are > 0 and MRR increased |
| **Contraction MRR** | Decrease from accounts that still pay | `previous MRR - MRR` where MRR > 0 and decreased |
| **Churned MRR** | MRR lost from accounts that stopped paying | Previous MRR of accounts whose MRR fell to 0 |
| **Reactivation MRR** | MRR from returning accounts that had churned | MRR of accounts paying again after a month at 0 |
| **Net New MRR** | Net change in MRR | `New + Reactivation + Expansion - Contraction - Churned` |
| **Active customers** | Accounts paying in the month | Count of accounts with MRR > 0 |
| **Logo churn rate** | Share of customers lost in the month | `Churned customers / customers paying last month` |
| **Gross revenue retention (GRR)** | Revenue kept from existing customers, ignoring upsell | `(Starting MRR - Contraction - Churned) / Starting MRR` |
| **Net revenue retention (NRR)** | Revenue kept from existing customers, including upsell | `(Starting MRR + Expansion - Contraction - Churned) / Starting MRR` |
| **ARPA** (Average Revenue Per Account) | Average MRR per paying customer | `MRR / Active customers` |

Integrity rules, enforced as dbt tests on every build:
- `Starting MRR + Net New MRR = MRR` for every month (`tests/assert_mrr_bridge_balances.sql`)
- Total MRR equals total billable invoice amounts (`tests/assert_mrr_reconciles_to_invoices.sql`)
- Rates stay between 0 and 1 (`tests/assert_rates_between_0_and_1.sql`)

## Product KPIs (`product.kpi_product_monthly`, `product.fct_feature_adoption_monthly`)

| KPI | Definition | Calculation |
|---|---|---|
| **MAU** (Monthly Active Users) | Distinct users with at least one event in the month | `count(distinct user_id)` |
| **DAU** (Daily Active Users) | Distinct users active on a day, averaged over the month | Average of daily distinct users |
| **DAU/MAU stickiness** | How often monthly users come back | `Average DAU / MAU` |
| **Active account rate** | Share of paying accounts that used the product | `Paying accounts with at least one event / paying accounts` |
| **Events per active user** | Depth of engagement | `Events / MAU` |
| **Feature adoption rate** | Share of active accounts using a feature | `Accounts using the feature / active accounts`, per feature per month |

## Data-quality rules (`quality.dq_rejected_records`)

Records excluded by validation are kept, with a reason, rather than silently dropped:

| Source | Rule |
|---|---|
| Billing invoices | Duplicate `invoice_id` (keep latest load) |
| Billing invoices | Currency must be `USD` after normalising case and whitespace |
| Billing invoices | Amount must not be negative |
| Product events | Event must belong to a known CRM account (no orphans) |
| CRM accounts | Duplicate account rows (keep latest load) |
