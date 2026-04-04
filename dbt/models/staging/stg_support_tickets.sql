select
    ticket_id,
    customer_id,
    product_id,
    cast(created_ts as timestamp) as created_ts,
    cast(created_date as date) as created_date,
    cast(closed_ts as timestamp) as closed_ts,
    lower(issue_type) as issue_type,
    lower(priority) as priority,
    lower(status) as status,
    cast(resolution_time_hours as double) as resolution_time_hours,
    cast(csat_score as integer) as csat_score,
    lower(channel) as channel,
    ticket_text,
    cast(ingested_at as timestamp) as ingested_at,
    source_file,
    cast(load_date as date) as load_date
from {{ source('raw', 'raw_support_tickets') }}
