-- Classifies each account-month into an MRR movement: new, expansion, contraction,
-- churn, reactivation or retained. This is the standard SaaS revenue bridge.
with base as (
    select
        *,
        lag(mrr_usd, 1, 0) over (partition by account_id order by month_start) as prev_mrr_usd,
        sum(case when mrr_usd > 0 then 1 else 0 end)
            over (partition by account_id order by month_start
                  rows between unbounded preceding and 1 preceding)            as prior_paying_months
    from {{ ref('int_account_mrr_monthly') }}
)

select
    account_id,
    month_start,
    mrr_usd,
    prev_mrr_usd,
    seats,
    case
        when mrr_usd > 0 and prev_mrr_usd = 0 and coalesce(prior_paying_months, 0) = 0 then 'new'
        when mrr_usd > 0 and prev_mrr_usd = 0                                       then 'reactivation'
        when mrr_usd = 0 and prev_mrr_usd > 0                                       then 'churn'
        when mrr_usd > prev_mrr_usd                                                 then 'expansion'
        when mrr_usd < prev_mrr_usd                                                 then 'contraction'
        else 'retained'
    end as movement_type,
    case when mrr_usd > 0 and prev_mrr_usd = 0 and coalesce(prior_paying_months, 0) = 0 then mrr_usd else 0 end as new_mrr_usd,
    case when mrr_usd > 0 and prev_mrr_usd = 0 and coalesce(prior_paying_months, 0) > 0 then mrr_usd else 0 end as reactivation_mrr_usd,
    case when prev_mrr_usd > 0 and mrr_usd > prev_mrr_usd then mrr_usd - prev_mrr_usd else 0 end as expansion_mrr_usd,
    case when mrr_usd > 0 and mrr_usd < prev_mrr_usd then prev_mrr_usd - mrr_usd else 0 end     as contraction_mrr_usd,
    case when mrr_usd = 0 and prev_mrr_usd > 0 then prev_mrr_usd else 0 end                     as churned_mrr_usd
from base
