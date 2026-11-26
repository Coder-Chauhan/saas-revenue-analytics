-- Calendar dimension used by every fact table (Power BI date table).
select
    cast(d as date)                         as date_day,
    cast(date_trunc('month', d) as date)    as month_start,
    year(d)                                 as year,
    quarter(d)                              as quarter,
    'Q' || quarter(d) || ' ' || year(d)     as quarter_label,
    month(d)                                as month_number,
    strftime(d, '%b %Y')                    as month_label,
    dayofweek(d)                            as day_of_week,
    dayofweek(d) in (0, 6)                  as is_weekend
from generate_series(date '2024-01-01', date '2026-12-31', interval 1 day) as t(d)
