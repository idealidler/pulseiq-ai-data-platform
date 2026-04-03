select
    o.order_date,
    p.category,
    c.region,
    count(distinct o.order_id) as orders_count,
    sum(o.quantity) as units_sold,
    round(sum(o.gross_amount), 2) as gross_revenue,
    round(sum(o.discount_amount), 2) as discounts,
    round(sum(o.net_amount), 2) as net_revenue,
    round(sum(o.refund_amount), 2) as refund_amount,
    round(
        case
            when sum(o.net_amount) = 0 then 0
            else sum(o.refund_amount) / sum(o.net_amount)
        end,
        4
    ) as refund_rate
from {{ ref('stg_orders') }} as o
left join {{ ref('stg_products') }} as p
    on o.product_id = p.product_id
left join {{ ref('stg_customers') }} as c
    on o.customer_id = c.customer_id
group by 1, 2, 3
