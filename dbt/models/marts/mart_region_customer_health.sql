with revenue as (
    select
        o.order_date as metric_date,
        c.region,
        count(distinct o.order_id) as orders_count,
        count(distinct o.customer_id) as unique_customers,
        sum(o.quantity) as units_sold,
        round(sum(o.gross_amount), 2) as gross_revenue,
        round(sum(o.net_amount), 2) as net_revenue,
        round(sum(o.refund_amount), 2) as refund_amount,
        sum(case when o.refund_flag then 1 else 0 end) as refund_orders_count,
        round(
            case
                when sum(o.net_amount) = 0 then 0
                else sum(o.refund_amount) / sum(o.net_amount)
            end,
            4
        ) as refund_rate
    from {{ ref('stg_orders') }} as o
    left join {{ ref('dim_customers') }} as c
        on o.customer_id = c.customer_id
    group by 1, 2
),
support as (
    select
        created_date as metric_date,
        region,
        count(*) as tickets_count,
        count(distinct customer_id) as complaint_customers,
        round(avg(resolution_time_hours), 2) as avg_resolution_time_hours,
        round(avg(csat_score), 2) as avg_csat_score,
        sum(case when status = 'open' then 1 else 0 end) as open_tickets_count
    from {{ ref('fct_support_tickets_enriched') }}
    group by 1, 2
)

select
    coalesce(r.metric_date, s.metric_date) as metric_date,
    coalesce(r.region, s.region) as region,
    coalesce(r.orders_count, 0) as orders_count,
    coalesce(r.unique_customers, 0) as unique_customers,
    coalesce(r.units_sold, 0) as units_sold,
    coalesce(r.gross_revenue, 0) as gross_revenue,
    coalesce(r.net_revenue, 0) as net_revenue,
    coalesce(r.refund_amount, 0) as refund_amount,
    coalesce(r.refund_orders_count, 0) as refund_orders_count,
    coalesce(r.refund_rate, 0) as refund_rate,
    coalesce(s.tickets_count, 0) as tickets_count,
    coalesce(s.complaint_customers, 0) as complaint_customers,
    coalesce(s.avg_resolution_time_hours, 0) as avg_resolution_time_hours,
    coalesce(s.avg_csat_score, 0) as avg_csat_score,
    coalesce(s.open_tickets_count, 0) as open_tickets_count
from revenue as r
full outer join support as s
    on r.metric_date = s.metric_date
    and r.region = s.region
