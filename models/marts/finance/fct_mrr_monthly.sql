-- One row per account per month with the MRR revenue bridge (grain: account x month).
select
    account_id,
    month_start,
    mrr_usd,
    prev_mrr_usd,
    seats,
    movement_type,
    new_mrr_usd,
    reactivation_mrr_usd,
    expansion_mrr_usd,
    contraction_mrr_usd,
    churned_mrr_usd,
    mrr_usd * 12 as arr_usd
from {{ ref('int_mrr_movements') }}
