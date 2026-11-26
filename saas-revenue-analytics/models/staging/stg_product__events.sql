-- One row per product event from known accounts. Orphan events are quarantined in
-- quality.dq_rejected_records instead of silently inflating usage metrics.
select
    e.event_id,
    e.account_id,
    e.user_id,
    cast(e.event_timestamp as timestamp)        as event_at,
    cast(cast(e.event_timestamp as timestamp) as date) as event_date,
    e.event_type,
    e.feature_id
from {{ source('raw', 'product_events') }} as e
inner join {{ ref('stg_crm__accounts') }} as a
    on e.account_id = a.account_id
