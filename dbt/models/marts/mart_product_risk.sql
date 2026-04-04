with revenue as (
    select
        o.order_date as metric_date,
        o.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        count(distinct o.order_id) as orders_count,
        sum(o.quantity) as units_sold,
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
    left join {{ ref('dim_products') }} as p
        on o.product_id = p.product_id
    group by 1, 2, 3, 4, 5
),
engagement as (
    select
        event_date as metric_date,
        product_id,
        total_events,
        sessions_count,
        active_customers,
        product_views,
        add_to_cart_events,
        checkout_start_events,
        purchase_events,
        support_page_views,
        product_view_to_purchase_rate
    from {{ ref('mart_product_engagement_daily') }}
),
support as (
    select
        created_date as metric_date,
        product_id,
        sum(tickets_count) as complaint_count,
        round(avg(avg_resolution_time_hours), 2) as avg_resolution_time_hours,
        round(avg(avg_csat_score), 2) as avg_csat_score,
        sum(open_tickets_count) as open_tickets_count
    from {{ ref('mart_support_issue_trends') }}
    group by 1, 2
)

select
    r.metric_date,
    r.product_id,
    r.product_name,
    r.category,
    r.subcategory,
    r.orders_count,
    r.units_sold,
    r.net_revenue,
    r.refund_amount,
    r.refund_rate,
    coalesce(e.total_events, 0) as total_events,
    coalesce(e.sessions_count, 0) as sessions_count,
    coalesce(e.active_customers, 0) as active_customers,
    coalesce(e.product_views, 0) as product_views,
    coalesce(e.add_to_cart_events, 0) as add_to_cart_events,
    coalesce(e.checkout_start_events, 0) as checkout_start_events,
    coalesce(e.purchase_events, 0) as purchase_events,
    coalesce(e.support_page_views, 0) as support_page_views,
    coalesce(e.product_view_to_purchase_rate, 0) as product_view_to_purchase_rate,
    coalesce(s.complaint_count, 0) as complaint_count,
    coalesce(s.avg_resolution_time_hours, 0) as avg_resolution_time_hours,
    coalesce(s.avg_csat_score, 0) as avg_csat_score,
    coalesce(s.open_tickets_count, 0) as open_tickets_count,
    round(
        (
            (coalesce(r.refund_rate, 0) * 0.35)
            + (least(coalesce(s.complaint_count, 0), 20) / 20.0 * 0.25)
            + ((1 - coalesce(e.product_view_to_purchase_rate, 0)) * 0.15)
            + (least(coalesce(e.support_page_views, 0), 50) / 50.0 * 0.10)
            + ((5 - coalesce(s.avg_csat_score, 5)) / 5.0 * 0.10)
            + (least(coalesce(s.open_tickets_count, 0), 10) / 10.0 * 0.05)
        ) * 100,
        2
    ) as risk_score
from revenue as r
left join engagement as e
    on r.metric_date = e.metric_date
    and r.product_id = e.product_id
left join support as s
    on r.metric_date = s.metric_date
    and r.product_id = s.product_id
