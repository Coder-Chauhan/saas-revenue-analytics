-- Share of active accounts using each feature per month (grain: feature x month).
with usage as (
    select
        cast(date_trunc('month', event_date) as date) as month_start,
        feature_id,
        account_id
    from {{ ref('stg_product__events') }}
    group by 1, 2, 3
),

active as (
    select month_start, count(distinct account_id) as active_accounts
    from usage
    group by 1
)

select
    u.month_start,
    u.feature_id,
    count(distinct u.account_id)                                          as accounts_using_feature,
    a.active_accounts,
    {{ safe_divide('count(distinct u.account_id)', 'a.active_accounts') }} as feature_adoption_rate
from usage as u
inner join active as a using (month_start)
group by u.month_start, u.feature_id, a.active_accounts
