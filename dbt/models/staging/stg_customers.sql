select
    customer_id,
    cast(signup_ts as timestamp) as signup_ts,
    initcap(region) as region,
    upper(country) as country,
    lower(segment) as segment,
    lower(acquisition_channel) as acquisition_channel,
    cast(is_active as boolean) as is_active,
    cast(ingested_at as timestamp) as ingested_at,
    source_file,
    cast(load_date as date) as load_date
from {{ source('raw', 'raw_customers') }}
