-- For every month: starting MRR + net new MRR = ending MRR.
select month_start, starting_mrr_usd, net_new_mrr_usd, mrr_usd
from {{ ref('kpi_revenue_monthly') }}
where abs(starting_mrr_usd + net_new_mrr_usd - mrr_usd) > 0.01
