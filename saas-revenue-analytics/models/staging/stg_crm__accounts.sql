-- One row per CRM account. Removes exact duplicate exports and standardises blanks.
with source as (
    select * from {{ source('raw', 'crm_accounts') }}
),

deduplicated as (
    select *,
           row_number() over (partition by account_id order by _loaded_at desc) as _row_num
    from source
)

select
    account_id,
    account_name,
    coalesce(nullif(trim(industry), ''), 'Unknown') as industry,
    segment,
    region,
    country,
    account_owner,
    cast(created_date as date)                      as created_date
from deduplicated
where _row_num = 1
