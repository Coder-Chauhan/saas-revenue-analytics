-- Every source record excluded by validation, with the reason. Keeps cleaning transparent
-- and auditable instead of silently dropping data.
with invoices as (
    select *,
           upper(trim(currency)) as currency_code,
           row_number() over (partition by invoice_id order by _loaded_at desc) as rn
    from {{ source('raw', 'billing_invoices') }}
)

select 'billing_invoices' as source_table, invoice_id as record_id, 'duplicate invoice_id' as reason
from invoices where rn > 1
union all
select 'billing_invoices', invoice_id, 'invalid currency code: ' || currency
from invoices where rn = 1 and currency_code <> 'USD'
union all
select 'billing_invoices', invoice_id, 'negative amount'
from invoices where rn = 1 and currency_code = 'USD' and cast(amount as decimal(12, 2)) < 0
union all
select 'product_events', event_id, 'orphan event: unknown account ' || e.account_id
from {{ source('raw', 'product_events') }} as e
where not exists (select 1 from {{ ref('stg_crm__accounts') }} as a where a.account_id = e.account_id)
union all
select 'crm_accounts', account_id, 'duplicate account row'
from (
    select account_id, row_number() over (partition by account_id order by _loaded_at desc) as rn
    from {{ source('raw', 'crm_accounts') }}
) as d
where rn > 1
