-- One row per valid invoice. Normalises currency codes, removes duplicate API records,
-- and drops rows that fail validation (they are kept for review in quality.dq_rejected_records).
with source as (
    select *,
           upper(trim(currency)) as currency_code,
           row_number() over (partition by invoice_id order by _loaded_at desc) as _row_num
    from {{ source('raw', 'billing_invoices') }}
)

select
    invoice_id,
    subscription_id,
    account_id,
    cast(invoice_date as date)       as invoice_date,
    cast(period_start as date)       as period_start,
    cast(seats as integer)           as seats,
    cast(amount as decimal(12, 2))   as amount_usd,
    currency_code,
    lower(status)                    as invoice_status
from source
where _row_num = 1
  and currency_code = 'USD'
  and cast(amount as decimal(12, 2)) >= 0
