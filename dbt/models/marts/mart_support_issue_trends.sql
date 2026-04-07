select
    created_date,
    product_id,
    product_name,
    category,
    issue_type,
    priority,
    count(*) as tickets_count,
    round(avg(resolution_time_hours), 2) as avg_resolution_time_hours,
    round(avg(csat_score), 2) as avg_csat_score,
    sum(case when status = 'open' then 1 else 0 end) as open_tickets_count
from {{ ref('fct_support_tickets_enriched') }}
group by 1, 2, 3, 4, 5, 6
