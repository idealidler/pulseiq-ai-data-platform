select
    product_id,
    product_name,
    lower(category) as category,
    lower(subcategory) as subcategory,
    cast(base_price as double) as base_price,
    cast(launch_ts as timestamp) as launch_ts,
    lower(status) as status,
    cast(ingested_at as timestamp) as ingested_at,
    source_file,
    cast(load_date as date) as load_date
from {{ source('raw', 'raw_products') }}
