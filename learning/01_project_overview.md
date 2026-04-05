# Chapter 1: Project Overview

## What PulseIQ is

PulseIQ is a data-engineering-first AI assistant built on top of a synthetic e-commerce and customer-support business dataset.

The system was built to demonstrate how an end-to-end data platform can power an AI chatbot that gives grounded answers.

It combines:

- synthetic source systems
- raw ingestion into Parquet
- warehouse modeling in DuckDB with dbt
- semantic retrieval over support-ticket text
- a tool-routed FastAPI backend
- a React frontend
- benchmark-based evaluation

## What business data exists in this project

The business domain is a simulated online commerce business with customer support.

The project includes:

- customers
- products
- orders and refunds
- behavioral events
- support tickets with free-text complaints

This means the system can answer questions about:

- sales and revenue
- refunds
- product performance
- support load
- customer complaint themes
- operational risk
- combined business metrics plus customer voice

## What makes this a data-engineering project

The chatbot is only the final interface.

Most of the project work lives in:

- source simulation
- ingestion
- Parquet storage
- DuckDB warehouse setup
- dbt transformations
- serving marts
- semantic indexing
- evaluation

That is important because the AI layer is only reliable when the data platform underneath it is well-structured.

## High-level architecture

The flow is:

1. source data is generated
2. ingestion writes raw Parquet and warehouse raw tables
3. dbt builds cleaned and serving-ready models
4. support ticket text is chunked and embedded
5. Qdrant stores vectors for semantic retrieval
6. the backend routes questions to SQL, vector search, or both
7. the frontend streams answers back to the user

## Main project folders

- `data_gen/`: synthetic source generation
- `ingestion/`: raw ingestion into Parquet and DuckDB
- `dbt/`: transformations and serving marts
- `embeddings/`: chunking, embeddings, indexing, retrieval
- `api/`: chat orchestration and tool routing
- `frontend/`: user-facing product experience
- `evals/`: benchmark suites and evaluation runner

## What success looks like in this project

The assistant is successful when it:

- chooses the right route: SQL, vector, or hybrid
- uses grounded evidence
- stays concise
- avoids unsupported claims
- answers common business questions reliably

Referenced files:

- [README.md](/Users/akshayjain/Documents/chat_bot/README.md)
- [frontend/src/App.tsx](/Users/akshayjain/Documents/chat_bot/frontend/src/App.tsx)
- [api/main.py](/Users/akshayjain/Documents/chat_bot/api/main.py)
