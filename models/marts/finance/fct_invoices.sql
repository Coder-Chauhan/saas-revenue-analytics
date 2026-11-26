-- One row per valid invoice (grain: invoice).
select
    invoice_id,
    subscription_id,
    account_id,
    invoice_date,
    period_start,
    seats,
    amount_usd,
    invoice_status,
    invoice_status in ('paid', 'open') as is_billable
from {{ ref('stg_billing__invoices') }}
