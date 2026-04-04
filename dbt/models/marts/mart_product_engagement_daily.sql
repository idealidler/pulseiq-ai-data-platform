select
    e.event_date,
    e.product_id,
    p.category,
    count(*) as total_events,
    count(distinct e.session_id) as sessions_count,
    count(distinct e.customer_id) as active_customers,
    sum(case when e.event_type = 'product_view' then 1 else 0 end) as product_views,
    sum(case when e.event_type = 'add_to_cart' then 1 else 0 end) as add_to_cart_events,
    sum(case when e.event_type = 'checkout_start' then 1 else 0 end) as checkout_start_events,
    sum(case when e.event_type = 'purchase' then 1 else 0 end) as purchase_events,
    sum(case when e.event_type = 'support_page_view' then 1 else 0 end) as support_page_views,
    round(
        case
            when sum(case when e.event_type = 'product_view' then 1 else 0 end) = 0 then 0
            else
                sum(case when e.event_type = 'purchase' then 1 else 0 end) * 1.0
                / sum(case when e.event_type = 'product_view' then 1 else 0 end)
        end,
        4
    ) as product_view_to_purchase_rate
from {{ ref('stg_events') }} as e
left join {{ ref('dim_products') }} as p
    on e.product_id = p.product_id
group by 1, 2, 3
