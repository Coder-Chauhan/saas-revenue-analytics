-- Rate KPIs must stay within valid bounds.
select month_start from {{ ref('kpi_revenue_monthly') }}
where logo_churn_rate not between 0 and 1 or gross_revenue_retention not between 0 and 1
union all
select month_start from {{ ref('kpi_product_monthly') }}
where dau_mau_stickiness not between 0 and 1
