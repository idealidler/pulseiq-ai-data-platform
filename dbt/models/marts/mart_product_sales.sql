select
    o.order_date as metric_date,
    o.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    count(distinct o.order_id) as orders_count,
    count(distinct o.customer_id) as unique_customers,
    sum(o.quantity) as units_sold,
    round(sum(o.gross_amount), 2) as gross_revenue,
    round(sum(o.discount_amount), 2) as discounts,
    round(sum(o.net_amount), 2) as net_revenue,
    sum(case when o.refund_flag then 1 else 0 end) as refund_orders_count,
    round(sum(o.refund_amount), 2) as refund_amount,
    round(
        case
            when sum(o.net_amount) = 0 then 0
            else sum(o.refund_amount) / sum(o.net_amount)
        end,
        4
    ) as refund_rate
from {{ ref('stg_orders') }} as o
left join {{ ref('dim_products') }} as p
    on o.product_id = p.product_id
group by 1, 2, 3, 4, 5
