-- Monthly recurring revenue (MRR) per account per month on a continuous month spine.
-- Months with no billable invoice get 0 MRR, which lets downstream models detect churn.
with billable as (
    select
        account_id,
        date_trunc('month', period_start)::date as month_start,
        sum(amount_usd)                         as mrr_usd,
        max(seats)                              as seats
    from {{ ref('stg_billing__invoices') }}
    where invoice_status in ('paid', 'open')          -- void invoices are not revenue
    group by 1, 2
),

bounds as (
    select
        account_id,
        min(month_start) as first_month,
        least(max(month_start) + interval 1 month,
              (select max(month_start) from billable))::date as last_month
    from billable
    group by 1
),

spine as (
    select
        b.account_id,
        cast(gs.month_start as date) as month_start
    from bounds as b,
         generate_series(b.first_month, b.last_month, interval 1 month) as gs(month_start)
)

select
    s.account_id,
    s.month_start,
    coalesce(m.mrr_usd, 0) as mrr_usd,
    coalesce(m.seats, 0)   as seats
from spine as s
left join billable as m
    on s.account_id = m.account_id
   and s.month_start = m.month_start
