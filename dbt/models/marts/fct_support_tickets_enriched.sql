select
    t.ticket_id,
    t.created_date,
    t.created_ts,
    t.closed_ts,
    t.customer_id,
    c.region,
    c.segment,
    t.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    t.issue_type,
    t.priority,
    t.status,
    t.resolution_time_hours,
    t.csat_score,
    t.channel,
    t.ticket_text
from {{ ref('stg_support_tickets') }} as t
left join {{ ref('dim_customers') }} as c
    on t.customer_id = c.customer_id
left join {{ ref('dim_products') }} as p
    on t.product_id = p.product_id
