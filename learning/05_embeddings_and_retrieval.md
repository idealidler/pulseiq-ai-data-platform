# Chapter 5: Embeddings and Retrieval

## Why SQL alone is not enough

SQL is excellent for:

- metrics
- aggregations
- rankings
- filters

But SQL is weak at understanding the meaning of complaint text.

Questions like:

- "What are customers saying about battery issues?"
- "What themes show up in refund complaints?"

need semantic retrieval, not just table filtering.

## What gets embedded in this project

The project embeds support ticket text.

The input comes from:

- `fct_support_tickets_enriched`

That table is used because it already contains:

- ticket text
- product context
- customer context
- region
- issue metadata

## Retrieval pipeline

The retrieval flow is:

1. load ticket rows from DuckDB
2. chunk ticket text
3. create embeddings with OpenAI
4. store vectors and metadata in Qdrant

Important metadata stored with vectors includes:

- ticket_id
- product_id
- product_name
- category
- region
- issue_type
- priority

This allows filtered semantic retrieval later.

## Why metadata filters matter

They make retrieval more precise.

For example:

- same product
- same category
- same region
- same issue type

This is especially important in hybrid questions where the assistant must not attach complaint evidence to the wrong product or region.

## Retrieval output

The retrieval layer returns semantic matches such as:

- text snippet
- ticket ID
- product
- issue type
- region
- similarity score

This output becomes evidence for the assistant.

Referenced files:

- [embeddings/data_source.py](/Users/akshayjain/Documents/chat_bot/embeddings/data_source.py)
- [embeddings/chunking.py](/Users/akshayjain/Documents/chat_bot/embeddings/chunking.py)
- [embeddings/indexer.py](/Users/akshayjain/Documents/chat_bot/embeddings/indexer.py)
- [embeddings/query.py](/Users/akshayjain/Documents/chat_bot/embeddings/query.py)
