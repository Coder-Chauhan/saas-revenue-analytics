-- One row per customer account, combining CRM attributes (CRM source) with
-- subscription and lifetime revenue attributes (billing source).
with mrr as (
    select
        account_id,
        min(case when mrr_usd > 0 then month_start end)                       as first_paid_month,
        max(case when mrr_usd > 0 then month_start end)                       as last_paid_month,
        sum(mrr_usd)                                                          as lifetime_revenue_usd,
        max_by(mrr_usd, month_start)                                          as current_mrr_usd
    from {{ ref('int_account_mrr_monthly') }}
    group by 1
)

select
    a.account_id,
    a.account_name,
    a.industry,
    a.segment,
    a.region,
    a.country,
    a.account_owner,
    a.created_date,
    s.subscription_id,
    s.plan,
    s.start_date            as subscription_start_date,
    s.end_date              as subscription_end_date,
    s.subscription_status,
    m.first_paid_month,
    m.last_paid_month,
    coalesce(m.lifetime_revenue_usd, 0) as lifetime_revenue_usd,
    coalesce(m.current_mrr_usd, 0)      as current_mrr_usd,
    coalesce(m.current_mrr_usd, 0) > 0  as is_active_customer
from {{ ref('stg_crm__accounts') }} as a
left join {{ ref('stg_billing__subscriptions') }} as s on a.account_id = s.account_id
left join mrr as m on a.account_id = m.account_id
