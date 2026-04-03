select
    customer_id,
    cast(signup_ts as date) as signup_date,
    region,
    country,
    segment,
    acquisition_channel,
    is_active
from {{ ref('stg_customers') }}
