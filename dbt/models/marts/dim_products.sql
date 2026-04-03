select
    product_id,
    product_name,
    category,
    subcategory,
    base_price,
    cast(launch_ts as date) as launch_date,
    status
from {{ ref('stg_products') }}
