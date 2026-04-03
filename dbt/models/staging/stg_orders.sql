select
    order_line_id,
    order_id,
    customer_id,
    product_id,
    cast(order_ts as timestamp) as order_ts,
    cast(order_date as date) as order_date,
    cast(quantity as integer) as quantity,
    cast(unit_price as double) as unit_price,
    cast(discount_amount as double) as discount_amount,
    cast(gross_amount as double) as gross_amount,
    cast(net_amount as double) as net_amount,
    cast(refund_flag as boolean) as refund_flag,
    cast(refund_amount as double) as refund_amount,
    lower(payment_method) as payment_method,
    cast(ingested_at as timestamp) as ingested_at,
    source_file,
    cast(load_date as date) as load_date
from {{ source('raw', 'raw_orders') }}
