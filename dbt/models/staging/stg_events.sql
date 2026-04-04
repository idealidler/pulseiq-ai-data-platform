select
    event_id,
    customer_id,
    session_id,
    cast(event_ts as timestamp) as event_ts,
    cast(event_date as date) as event_date,
    lower(event_type) as event_type,
    product_id,
    lower(page_name) as page_name,
    lower(device_type) as device_type,
    lower(traffic_source) as traffic_source,
    json_extract_string(metadata_json, '$.campaign_id') as campaign_id,
    json_extract_string(metadata_json, '$.feature_name') as feature_name,
    json_extract_string(metadata_json, '$.referrer') as referrer,
    metadata_json,
    cast(ingested_at as timestamp) as ingested_at,
    source_file,
    cast(load_date as date) as load_date
from {{ source('raw', 'raw_events') }}
