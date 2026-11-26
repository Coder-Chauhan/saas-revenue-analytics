-- One row per subscription from the billing API.
select
    subscription_id,
    account_id,
    plan,
    cast(start_date as date)                    as start_date,
    cast(nullif(cast(end_date as varchar), '') as date) as end_date,
    lower(status)                               as subscription_status,
    billing_interval
from {{ source('raw', 'billing_subscriptions') }}
