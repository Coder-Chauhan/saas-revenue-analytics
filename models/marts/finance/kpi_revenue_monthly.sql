-- Company-level revenue KPIs per month. Definitions are documented in docs/kpi_definitions.md.
with monthly as (
    select
        month_start,
        sum(mrr_usd)                                           as mrr_usd,
        sum(prev_mrr_usd)                                      as starting_mrr_usd,
        sum(new_mrr_usd)                                       as new_mrr_usd,
        sum(reactivation_mrr_usd)                              as reactivation_mrr_usd,
        sum(expansion_mrr_usd)                                 as expansion_mrr_usd,
        sum(contraction_mrr_usd)                               as contraction_mrr_usd,
        sum(churned_mrr_usd)                                   as churned_mrr_usd,
        count(distinct case when mrr_usd > 0 then account_id end)      as active_customers,
        count(distinct case when prev_mrr_usd > 0 then account_id end) as starting_customers,
        count(distinct case when movement_type = 'new' then account_id end)   as new_customers,
        count(distinct case when movement_type = 'churn' then account_id end) as churned_customers
    from {{ ref('fct_mrr_monthly') }}
    group by 1
)

select
    month_start,
    mrr_usd,
    mrr_usd * 12                                                          as arr_usd,
    starting_mrr_usd,
    new_mrr_usd,
    reactivation_mrr_usd,
    expansion_mrr_usd,
    contraction_mrr_usd,
    churned_mrr_usd,
    new_mrr_usd + reactivation_mrr_usd + expansion_mrr_usd
        - contraction_mrr_usd - churned_mrr_usd                           as net_new_mrr_usd,
    active_customers,
    new_customers,
    churned_customers,
    {{ safe_divide('churned_customers', 'starting_customers') }}          as logo_churn_rate,
    {{ safe_divide('starting_mrr_usd - contraction_mrr_usd - churned_mrr_usd', 'starting_mrr_usd') }}
                                                                          as gross_revenue_retention,
    {{ safe_divide('starting_mrr_usd + expansion_mrr_usd - contraction_mrr_usd - churned_mrr_usd', 'starting_mrr_usd') }}
                                                                          as net_revenue_retention,
    {{ safe_divide('mrr_usd', 'active_customers') }}                      as arpa_usd
from monthly
