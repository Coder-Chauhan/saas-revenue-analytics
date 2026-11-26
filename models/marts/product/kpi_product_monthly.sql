-- Company-level product engagement KPIs per month.
with events as (
    select *, cast(date_trunc('month', event_date) as date) as month_start
    from {{ ref('stg_product__events') }}
),

monthly as (
    select
        month_start,
        count(distinct user_id)    as monthly_active_users,
        count(distinct account_id) as active_accounts,
        count(*)                   as events
    from events
    group by 1
),

daily as (
    select month_start, avg(dau) as avg_daily_active_users
    from (
        select month_start, event_date, count(distinct user_id) as dau
        from events
        group by 1, 2
    ) as d
    group by 1
),

paying_accounts as (
    select month_start, account_id
    from {{ ref('fct_mrr_monthly') }}
    where mrr_usd > 0
),

paying as (
    select
        p.month_start,
        count(distinct p.account_id)                                       as paying_accounts,
        count(distinct case when e.account_id is not null then p.account_id end) as active_paying_accounts
    from paying_accounts as p
    left join (select distinct month_start, account_id from events) as e
        on p.month_start = e.month_start and p.account_id = e.account_id
    group by 1
)

select
    m.month_start,
    m.monthly_active_users,
    d.avg_daily_active_users,
    {{ safe_divide('d.avg_daily_active_users', 'm.monthly_active_users') }} as dau_mau_stickiness,
    m.active_accounts,
    p.paying_accounts,
    p.active_paying_accounts,
    {{ safe_divide('p.active_paying_accounts', 'p.paying_accounts') }}     as active_account_rate,
    {{ safe_divide('m.events', 'm.monthly_active_users') }}                as events_per_active_user
from monthly as m
left join daily as d using (month_start)
left join paying as p using (month_start)
