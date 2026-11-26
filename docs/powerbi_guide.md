# Power BI Report Guide

How to build the report from the exported star schema in about an hour.

## 1. Load the data

1. Run `./run_pipeline.sh` (or `python scripts/export_for_powerbi.py`) to create `exports/powerbi/*.csv`.
2. Power BI Desktop > **Get Data > Text/CSV**, and load every file in `exports/powerbi/`.
3. In Power Query, check the types: `month_start`, `date_day`, `event_date`, `invoice_date` should be **Date**; the `*_usd` columns **Decimal number**; and the `*_rate`, `*_retention` and `stickiness` columns **Decimal number** (format them as percentages in the model view).

## 2. Model (star schema)

Select `dim_date` > **Mark as date table** (date column: `date_day`). Then create these relationships (Model view, single direction, many-to-one):

| From (many) | To (one) |
|---|---|
| `fct_mrr_monthly[month_start]` | `dim_date[date_day]` |
| `fct_mrr_monthly[account_id]` | `dim_customers[account_id]` |
| `fct_invoices[invoice_date]` | `dim_date[date_day]` |
| `fct_invoices[account_id]` | `dim_customers[account_id]` |
| `fct_product_usage_daily[event_date]` | `dim_date[date_day]` |
| `fct_product_usage_daily[account_id]` | `dim_customers[account_id]` |
| `fct_product_usage_daily[feature_id]` | `dim_features[feature_id]` |
| `fct_feature_adoption_monthly[feature_id]` | `dim_features[feature_id]` |
| `kpi_revenue_monthly[month_start]` | `dim_date[date_day]` |
| `kpi_product_monthly[month_start]` | `dim_date[date_day]` |

Hide the key columns on the fact tables so report users filter through the dimensions.

## 3. DAX measures

Create a blank table called `_Measures`, then add the following measures. They work against
`fct_mrr_monthly`, so every KPI can be sliced by segment, region, industry, plan or owner.

```DAX
MRR = SUM ( fct_mrr_monthly[mrr_usd] )

ARR = [MRR] * 12

Starting MRR = SUM ( fct_mrr_monthly[prev_mrr_usd] )

New MRR = SUM ( fct_mrr_monthly[new_mrr_usd] )

Expansion MRR = SUM ( fct_mrr_monthly[expansion_mrr_usd] )

Contraction MRR = SUM ( fct_mrr_monthly[contraction_mrr_usd] )

Churned MRR = SUM ( fct_mrr_monthly[churned_mrr_usd] )

Reactivation MRR = SUM ( fct_mrr_monthly[reactivation_mrr_usd] )

Net New MRR =
    [New MRR] + [Reactivation MRR] + [Expansion MRR] - [Contraction MRR] - [Churned MRR]

Active Customers =
    CALCULATE ( DISTINCTCOUNT ( fct_mrr_monthly[account_id] ), fct_mrr_monthly[mrr_usd] > 0 )

Starting Customers =
    CALCULATE ( DISTINCTCOUNT ( fct_mrr_monthly[account_id] ), fct_mrr_monthly[prev_mrr_usd] > 0 )

Churned Customers =
    CALCULATE ( DISTINCTCOUNT ( fct_mrr_monthly[account_id] ), fct_mrr_monthly[movement_type] = "churn" )

Logo Churn Rate = DIVIDE ( [Churned Customers], [Starting Customers] )

Gross Revenue Retention =
    DIVIDE ( [Starting MRR] - [Contraction MRR] - [Churned MRR], [Starting MRR] )

Net Revenue Retention =
    DIVIDE ( [Starting MRR] + [Expansion MRR] - [Contraction MRR] - [Churned MRR], [Starting MRR] )

ARPA = DIVIDE ( [MRR], [Active Customers] )

MRR MoM % =
    VAR prev = CALCULATE ( [MRR], DATEADD ( dim_date[date_day], -1, MONTH ) )
    RETURN DIVIDE ( [MRR] - prev, prev )

Monthly Active Users = SUM ( kpi_product_monthly[monthly_active_users] )

Active Account Rate = AVERAGE ( kpi_product_monthly[active_account_rate] )

DAU/MAU Stickiness = AVERAGE ( kpi_product_monthly[dau_mau_stickiness] )

Feature Adoption Rate =
    DIVIDE (
        SUM ( fct_feature_adoption_monthly[accounts_using_feature] ),
        SUM ( fct_feature_adoption_monthly[active_accounts] )
    )

Rejected Records = COUNTROWS ( dq_rejected_records )
```

Format the currency measures as `$#,0` and the rate measures as `0.0%`.
For monthly views, put `dim_date[month_label]` on the axis and sort it by `dim_date[month_start]`.

## 4. Report pages

**Page 1: Executive summary (for senior leaders)**
- KPI cards: ARR, MRR, MRR MoM %, Active Customers, Net Revenue Retention, Logo Churn Rate
- Line chart: MRR by month
- Waterfall chart: MRR bridge for the selected month (Starting MRR, New, Expansion, Contraction, Churned)
- Slicers: month, region, segment

**Page 2: Revenue operations (for operational users)**
- Stacked column: New / Expansion / Contraction / Churned MRR by month
- Matrix: MRR, ARPA and churn by segment and region
- Table: top 20 customers by current MRR (from `dim_customers`), with plan and owner
- Bar chart: churned MRR by industry

**Page 3: Product usage and adoption**
- KPI cards: Monthly Active Users, DAU/MAU Stickiness, Active Account Rate
- Line chart: MAU and active account rate by month
- Bar chart: feature adoption rate by feature (from `fct_feature_adoption_monthly`)
- Table: paying accounts with no product usage this month (churn-risk list)

**Page 4: Data quality**
- Card: Rejected Records
- Table: `dq_rejected_records` grouped by source and reason

## 5. Publish

Save as `reports/saas_analytics.pbix`, publish to the Power BI Service, and add screenshots of each page to the README.
