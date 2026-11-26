-- Product usage per account, feature and day (grain: account x feature x day).
select
    account_id,
    feature_id,
    event_date,
    count(*)                                                   as events,
    count(distinct user_id)                                    as active_users,
    count(*) filter (where event_type = 'report_run')          as reports_run,
    count(*) filter (where event_type = 'export')              as exports
from {{ ref('stg_product__events') }}
group by 1, 2, 3
