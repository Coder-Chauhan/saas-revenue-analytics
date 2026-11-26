-- Total MRR in the revenue bridge must equal total billable invoice amounts.
-- Returns a row (test failure) if they differ by more than one cent.
with bridge as (select sum(mrr_usd) as total from {{ ref('fct_mrr_monthly') }}),
     invoices as (select sum(amount_usd) as total from {{ ref('fct_invoices') }} where is_billable)
select bridge.total as bridge_total, invoices.total as invoice_total
from bridge, invoices
where abs(bridge.total - invoices.total) > 0.01
