# PulseIQ

PulseIQ is a data-engineering-first AI chatbot project built to demonstrate an end-to-end modern data platform:

- synthetic upstream source systems
- raw ingestion into Parquet
- DuckDB warehouse modeling with dbt
- semantic metadata defined inside dbt
- semantic retrieval over support tickets with OpenAI embeddings + Qdrant
- a tool-routed FastAPI chat backend
- a polished React frontend with a product tab and an architecture tab
- deterministic benchmark suites for quality measurement
- project-specific learning notes for NotebookLM and self-study

The project is intentionally honest about what it is: a serious learning build that still behaves like a real product.

## What It Does

PulseIQ answers questions like:

- Which is the highest selling product?
- Which customer has filed the most refunds?
- Which products have the highest risk score?
- What are customers complaining about in electronics?
- Which products have both high support page views and rising complaints?
- What are the biggest operational risks right now?

It combines:

- SQL-based reasoning over serving marts
- vector search over support-ticket text
- hybrid answers when both structured metrics and semantic evidence are needed

## Architecture

The system follows a layered pattern:

1. `data_gen/`
   - Generates synthetic `customers`, `products`, `orders`, `events`, and `support_tickets`
2. `ingestion/`
   - Lands source files into raw Parquet with ingestion metadata
   - Registers raw tables in DuckDB
3. `dbt/`
   - Builds staging models and serving marts
   - Stores semantic meaning in model descriptions, column descriptions, and `meta.ai_hint`
   - Key marts include `mart_product_sales`, `mart_product_risk`, `mart_region_customer_health`, `mart_product_engagement_daily`, and `mart_support_issue_trends`
4. `embeddings/`
   - Reads enriched support tickets
   - Chunks text
   - Creates embeddings
   - Indexes vectors in Qdrant
5. `api/`
   - FastAPI chat backend
   - Reads dbt metadata at runtime to build schema context for the assistant
   - Routes questions to SQL, vector, or hybrid workflows
   - Supports streaming chat responses
6. `frontend/`
   - React + TypeScript + Vite + Tailwind UI
   - Product experience tab + architecture walkthrough tab
7. `evals/`
   - Deterministic benchmark suite for route accuracy, evidence use, and answer quality
8. `learning/`
   - Curated project walkthrough notes for NotebookLM and chapter-by-chapter learning

## Tech Stack

- Python
- DuckDB
- dbt
- Parquet
- OpenAI API
- Qdrant
- FastAPI
- React
- TypeScript
- Vite
- Tailwind CSS

## Repo Structure

```text
api/            FastAPI backend and tool orchestration
data/           Generated sources, raw data, warehouse, vector store
data_gen/       Synthetic data generators
dbt/            Warehouse models and tests
embeddings/     Chunking, indexing, and semantic retrieval
evals/          Benchmark test cases and evaluation runner
frontend/       React frontend
ingestion/      Source-to-raw ingestion pipeline
learning/       Project-specific learning notes and architecture chapters
```

## Local Setup

### 1. Python environment

```bash
pip install -r requirements.txt
```

### 2. Environment variables

Create a local `.env` in the repo root using `.env.example` as a guide.

Required:

- `OPENAI_API_KEY`

Useful optional values:

- `CHAT_MODEL=gpt-4o-mini`
- `EMBEDDING_MODEL=text-embedding-3-small`

### 3. Frontend environment

Optional: create `frontend/.env` from `frontend/.env.example` if you want to point the UI at a non-default API URL.

## End-to-End Run

Run the full stack in this order:

```bash
python3 -m data_gen.main
python3 -m ingestion.main
dbt build --project-dir dbt --profiles-dir dbt
python3 -m embeddings.main
uvicorn api.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

## Evaluation

Run benchmark evals with:

```bash
python3 -m evals.run --suite top20
```

The eval runner checks:

- route choice: `sql`, `vector`, or `hybrid`
- required tool usage
- evidence presence
- keyword alignment
- answer conciseness

Results are written under `evals/results/`.

Current project benchmark highlights:

- `top20` suite reached `20/20` perfect cases
- `route_accuracy: 1.0`
- `conciseness_rate: 1.0`

## Outputs

The project produces:

- source CSV and JSONL under `data/source/`
- raw Parquet under `data/raw/`
- DuckDB warehouse at `data/warehouse/pulseiq.duckdb`
- Qdrant vector store under `data/vector/`

## Frontend Experience

The frontend has two tabs:

- `Experience`
  - production-style product page
  - floating chatbot widget
  - streamed responses
- `Architecture`
  - visual system map of the exact stack behind the assistant

## Semantic Layer

PulseIQ does not keep the assistant's table knowledge only in the prompt.

Instead:

- dbt `schema.yml` stores model descriptions and column descriptions
- `meta.ai_hint` stores compact AI-facing metadata such as grain, role, metrics, and dimensions
- `api/services/schema_context.py` reads that metadata at runtime
- the chat backend injects the generated schema context into the assistant

This keeps the semantic meaning closer to the data model and reduces drift between the warehouse and the AI layer.

## Learning Pack

If you want to study the project chapter by chapter or import it into NotebookLM, use the files under `learning/`.

They explain:

- data generation and ingestion
- dbt transformations and serving models
- semantic metadata and schema context
- embeddings and retrieval
- chat orchestration
- evaluation
- frontend behavior
- end-to-end request flow

## Notes

- This project is optimized for local development and demonstration.
- The assistant is grounded through serving marts and semantic retrieval, not raw source tables.
- Generated data is synthetic by design so the system architecture can be explored safely and at scale.
