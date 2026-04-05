# Chapter 3: dbt Transformations and Serving Models

## Why dbt is central in this project

dbt is where raw warehouse data becomes business-ready analytical data.

The important shift is:

- raw tables are close to source systems
- dbt models shape that data into stable business meaning

In this project, dbt is not used just for analytics dashboards.
It is also used to prepare reliable data for the AI assistant.

## Layering inside dbt

This project uses a layered modeling approach:

- staging models
- dimensions and enriched facts
- serving marts

### Staging models

These clean and standardize raw data.

Examples:

- `stg_customers`
- `stg_products`
- `stg_orders`
- `stg_events`
- `stg_support_tickets`

Their purpose is:

- type casting
- renaming
- standardization
- preserving source grain

### Dimensions and enriched facts

These are reusable semantic building blocks.

Examples:

- `dim_customers`
- `dim_products`
- `fct_support_tickets_enriched`

`fct_support_tickets_enriched` is especially important because it brings ticket, product, and customer context together in one table.

### Serving marts

These are the most important models for the chatbot.

They were designed so the assistant does not have to invent complex joins or business logic at runtime.

Examples:

- `mart_product_risk`
- `mart_product_sales`
- `mart_region_customer_health`
- `mart_product_engagement_daily`
- `mart_support_issue_trends`
- `mart_revenue_daily`

## Why serving models matter for AI

Serving models improve:

- query speed
- answer consistency
- correctness of business logic
- benchmark reliability
- prompt simplicity

For example:

- `mart_product_sales` is used for product sales ranking questions
- `mart_product_risk` is used for operational and product-risk questions
- `mart_region_customer_health` is used for regional health questions
- `mart_support_issue_trends` is used for issue-type support trend questions

Without these serving models, the assistant would have to:

- infer which raw tables to use
- infer join logic
- infer metric definitions
- rebuild the same logic again and again

That would be slower and less reliable.

## A key design decision in this project

The project deliberately moves business logic into dbt rather than into prompt text.

That means:

- dbt owns the semantic business layer
- the chatbot consumes that layer

This is much closer to a production pattern than letting the model build everything from raw tables.

Referenced files:

- [dbt/models/schema.yml](/Users/akshayjain/Documents/chat_bot/dbt/models/schema.yml)
- [dbt/models/marts/mart_product_risk.sql](/Users/akshayjain/Documents/chat_bot/dbt/models/marts/mart_product_risk.sql)
- [dbt/models/marts/mart_product_sales.sql](/Users/akshayjain/Documents/chat_bot/dbt/models/marts/mart_product_sales.sql)
- [dbt/models/marts/mart_region_customer_health.sql](/Users/akshayjain/Documents/chat_bot/dbt/models/marts/mart_region_customer_health.sql)
