# Chapter 7: Evaluation and Quality

## Why evaluation exists in this project

Without evaluation, a chatbot can look good in a few demos while failing on real user questions.

This project uses benchmark-based evaluation to measure reliability.

## What is evaluated

The eval runner checks things like:

- route correctness
- tool usage
- evidence presence
- keyword alignment
- conciseness

This is not a full human-quality evaluation system, but it is a practical regression framework.

## Benchmark suites in this project

The project contains multiple benchmark sets, including:

- baseline
- v2
- top20

The `top20` suite is especially useful because it contains realistic business questions such as:

- highest selling product
- customer with most refunds
- support issue load
- customer complaint themes

## Why this matters for engineering

Evaluation exposed real system gaps, including:

- missing serving tables
- routing failures
- insufficient grounding

Several architectural improvements in this project came directly from benchmark failures.

That includes:

- adding `mart_product_sales`
- adding `mart_region_customer_health`
- improving hybrid routing
- moving semantic meaning into dbt metadata

## Main lesson

Evaluation is not a reporting add-on.

It is part of system design.

Referenced files:

- [evals/run.py](/Users/akshayjain/Documents/chat_bot/evals/run.py)
- [evals/test_cases_top20.json](/Users/akshayjain/Documents/chat_bot/evals/test_cases_top20.json)
