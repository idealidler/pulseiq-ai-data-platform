# Chatbot Project: Challenges & Solutions

## Project Overview
Built an AI-powered chatbot that answers business questions by combining structured SQL queries with semantic vector search. The system uses OpenAI's gpt-4o-mini model with few-shot learning (golden SQL examples) to generate relevant queries and retrieve customer support evidence.

---

## Challenge 1: Golden SQL Examples Not Reaching OpenAI

### Problem
- **Symptom**: Golden SQL examples were successfully stored in Qdrant vector database but weren't being retrieved and sent to OpenAI API calls
- **Impact**: LLM lacked few-shot examples to learn query patterns, resulting in poorly generated SQL queries
- **Discovery**: Analyzed OpenAI API logs and noticed system prompt only contained instruction header, no actual golden query examples

### Root Cause
The vector search retrieval function in `embeddings/query.py` had **hardcoded field extraction logic** designed specifically for support tickets:
```python
# OLD CODE - only extracted support ticket fields
result_item = {
    "ticket_id": payload.get("ticket_id"),
    "text": payload.get("text"),
    "product_id": payload.get("product_id")
}
```

When querying the `sql_examples` collection, this extraction skipped the `question` and `sql` fields that contained the actual examples.

### Solution
Implemented **dynamic payload extraction** to preserve all fields from any Qdrant collection:
```python
# NEW CODE - extracts all payload fields
result_item = {"score": hit.score}
result_item.update(payload)  # Preserves all fields regardless of collection
```

### Impact
- ✅ Golden SQL examples now properly formatted in system prompt
- ✅ Improved answer quality (LLM learned from examples)
- ✅ Reduced hallucinated SQL queries
- ✅ Single function works for both support_tickets AND sql_examples collections

### Interview Talking Points
- "Debugged payload extraction - realized hardcoded field extraction was too specific"
- "Switched to dynamic extraction using result_item.update(payload)"
- "This was a coupling issue - the function was tightly tied to one collection schema"

---

## Challenge 2: Wrong Products in Feedback (Data Cross-Contamination)

### Problem
- **Symptom**: CSAT question "What products have the lowest CSAT?" returned products 473, 246, 102 but displayed feedback from completely different products (442, 288, 461)
- **Impact**: Answers were factually incorrect and misrepresented customer sentiment
- **Severity**: Critical - data integrity issue

### Root Cause
The SQL queries in `data/golden_sql.json` did **not include product_id in their SELECT statements**:
```sql
-- OLD QUERY (WRONG)
SELECT product_name, COUNT(*) as support_count
FROM fct_support_tickets
GROUP BY product_name
-- No product_id! Can't match vector results later

-- NEW QUERY (CORRECT)
SELECT product_id, product_name, COUNT(*) as support_count
FROM fct_support_tickets
GROUP BY product_id, product_name
```

Without `product_id`, the answer composition logic couldn't filter vector search results to match the SQL results.

### Solution
Implemented **multi-layer filtering** to prevent cross-contamination:

1. **Updated 6 SQL queries** in golden_sql.json to include product_id in SELECT and GROUP BY
2. **Re-seeded Qdrant** golden_sql collection with corrected queries
3. **Added product_id filtering** in answer composition (`_compose_grounded_answer`):
```python
# Extract allowed product IDs from SQL results
allowed_product_ids = {str(row.get("product_id")) for row in sql_rows}

# Filter vector evidence to ONLY these products
filtered_matches = {
    pid: matches for pid, matches in matches_by_product.items()
    if str(pid) in allowed_product_ids
}
```

### Impact
- ✅ Products in feedback now match SQL results exactly
- ✅ No data leakage between products
- ✅ Answers are factually correct

### Interview Talking Points
- "Discovered that SQL queries were missing product_id in the SELECT clause"
- "Implemented multi-layer filtering: SQL query → allowed_product_ids → evidence matching"
- "This revealed importance of data lineage - need to track IDs through entire pipeline"

---

## Challenge 3: Duplicate Evidence Collection (Inefficient API Calls)

### Problem
- **Symptom**: For CSAT questions, chatbot was showing 7 evidence items instead of expected 4 (1 SQL + 3 product-filtered vector searches)
- **Root Cause**: LLM was independently calling vector search for the same products multiple times
- **Impact**: Wasting API tokens, increasing latency, unnecessary Qdrant queries

### Architecture Problem
The system had a **supplementary_search_done flag** to prevent duplicate searches:
```python
# Flag added to prevent supplementary search after SQL execution
if route == "sql" and not supplementary_search_done:
    _supplement_hybrid_vector_evidence()
    supplementary_search_done = True
```

However, the flag only prevented **function-level calls**, not **LLM's independent calls**.

**Flow that caused duplicates:**
1. **Round 1**: LLM calls SQL → route = "sql" → supplementary search triggered (adds 2-3 vector results for products 473, 246, 102)
2. **Round 2**: LLM independently calls `run_vector_search` with product_id filters for same products → adds 3 more results
3. **Total**: 1 SQL + 2 supplementary + 3 LLM calls = 6 vectors + 1 SQL = 7 items

### Solution
Implemented **evidence-level deduplication** (data-level check, not function-level):

1. **Added helper function** `_should_add_vector_evidence()`:
```python
def _should_add_vector_evidence(evidence: list[dict], product_id_filter: str | None) -> bool:
    """Check if this product_id already has vector evidence"""
    if not product_id_filter:
        return True
    
    # Extract existing product IDs from collected evidence
    existing_product_ids = {
        str(match.get("product_id"))
        for item in evidence
        if item["tool"] == "run_vector_search"
        for match in item["result"]
        if match.get("product_id")
    }
    
    return str(product_id_filter) not in existing_product_ids
```

2. **Modified evidence collection logic** to check before adding:
```python
if call.name == "run_vector_search":
    filters = arguments.get("filters", {})
    product_id_filter = filters.get("product_id")
    
    if _should_add_vector_evidence(evidence, product_id_filter):
        # Add to evidence
        evidence.append({"tool": call.name, "result": result})
    else:
        # Return error to LLM (teaches it not to re-search)
        return {"error": "Product already has vector evidence"}
```

### Impact
- ✅ Reduced from 7 → 4 evidence items (33% reduction)
- ✅ 3 fewer unnecessary vector searches per question
- ✅ Lower API costs and latency
- ✅ LLM learns from error responses not to duplicate searches

### Interview Talking Points
- "Function-level guards don't prevent LLM's independent calls - switched to data-level deduplication"
- "Added _should_add_vector_evidence() to check for duplicates at point of collection"
- "When LLM tried duplicate searches, it got error responses that trained it not to repeat"
- "This is an example of managing LLM behavior through feedback loops"

---

## Challenge 4: Duplicate Complaint Text Display

### Problem
- **Symptom**: When showing customer complaint examples, identical text was displayed twice:
```
Apparel Item 473
Example: "I need help with a return and refund for this item."
Example: "I need help with a return and refund for this item."  ← Duplicate!
```
- **Root Cause**: Vector search returned top-2 matches per product, and Qdrant sometimes returned duplicate or very similar tickets
- **Impact**: Poor UX - redundant information making answers look low-quality

### Root Cause Analysis
The answer formatting code showed all vector matches (up to 2 per product) without deduplicating at the text level:
```python
# OLD CODE - shows all matches
for match in matches:
    text = str(match.get("text", "")).strip()
    if text:
        lines.append(f'  - Example: "{text}"')  # No dedup check!
```

### Solution
Implemented **text-level deduplication** using a set:
```python
# NEW CODE - deduplicates at text level
seen_texts = set()
for match in matches:
    text = str(match.get("text", "")).strip()
    if text and text not in seen_texts:  # Skip if already shown
        lines.append(f'  - Example: "{text}"')
        seen_texts.add(text)
```

### Impact
- ✅ Eliminated duplicate complaint displays
- ✅ Maintains diversity if different complaints exist
- ✅ Improved user experience

### Interview Talking Points
- "Identified that vector search was returning semantically similar tickets"
- "Added deduplication at display level to show only unique complaint texts"
- "Preserved ability to show multiple distinct complaints for same product"

---

## Challenge 5: System Prompt Quality & Production-Grade Guidance

### Problem
- **Symptom**: LLM wasn't consistently:
  - Showing human-readable names (product_name) instead of IDs
  - Handling NULL/missing data gracefully
  - Following golden SQL examples
  - Restricting unfiltered vector searches for product-specific questions

### Solution
Implemented comprehensive system prompt improvements:

1. **Added product_name priority rule**:
```
"always show human-readable names (product_name, region, customer_name) 
instead of IDs whenever possible"
```

2. **Added NULL handling guidance**:
```
"When expected metric columns are NULL or return zero results, 
respond that 'data is unavailable' rather than showing zero"
```

3. **Improved golden SQL formatting** with code blocks and emojis:
```
⚠️ SQL Example:
```sql
SELECT product_id, product_name, COUNT(*) as complaint_count
FROM fct_support_tickets
GROUP BY product_id, product_name
```
```

4. **Added dynamic question guidance** via `_question_guidance()`:
- For CSAT/refund questions: "Use product_id filters to avoid data contamination"
- Schema context automatically injected based on question type

### Impact
- ✅ LLM follows examples more consistently
- ✅ Graceful handling of edge cases (NULLs, empty results)
- ✅ Better structured answers with product-specific evidence

---

## Technical Lessons Learned

### 1. Data Lineage Matters
**Lesson**: IDs must flow through entire pipeline (SQL → collection → filtering → display)
- Ensure every data transformation preserves identity fields
- Don't assume data relationships can be inferred at display time

### 2. Guard Function-Level AND Data-Level
**Lesson**: Function-level guards aren't enough when LLM makes independent tool calls
- Add data-level checks at collection points
- Teach LLM through error responses (feedback loop)
- Evidence-level deduplication > flag-based deduplication

### 3. Schema Coupling is a Liability
**Lesson**: Hardcoded field extraction (ticket-specific) breaks when querying different collections
- Use dynamic extraction (`result_item.update(payload)`)
- Keep functions generic and collection-agnostic

### 4. Prompt Engineering Requires Multiple Layers
**Lesson**: Single system prompt isn't enough for complex behavior
- Layer 1: Base SYSTEM_PROMPT (grounding rules)
- Layer 2: Schema context (available tables, columns)
- Layer 3: Golden SQL examples (few-shot learning)
- Layer 4: Dynamic guidance (question-specific rules)

### 5. Display Deduplication Complements Logical Deduplication
**Lesson**: Prevent duplicates at source (evidence collection) AND display (text level)
- Reduces API waste (fewer unnecessary queries)
- Improves UX (no redundant information)

---

## Interview Summary

### Key Achievements
✅ Fixed golden SQL retrieval pipeline (payload extraction)  
✅ Eliminated data cross-contamination (product filtering)  
✅ Reduced API calls by 33% (evidence deduplication)  
✅ Improved answer quality (system prompt refinements)  
✅ Enhanced UX (display deduplication)  

### Key Skills Demonstrated
- **Debugging**: Traced API logs to identify missing golden SQL examples
- **Data Engineering**: Implemented multi-layer filtering to prevent data leakage
- **Architecture**: Recognized function-level guards insufficient, designed data-level deduplication
- **LLM Orchestration**: Managed LLM behavior through system prompts and error feedback loops
- **Problem Solving**: Methodical root cause analysis using debug scripts and subagent research

### Interview Narrative
*"While building this chatbot, I encountered several integration challenges that forced me to think deeply about data integrity, API efficiency, and LLM behavior management. The journey from fixing payload extraction bugs to implementing evidence-level deduplication shows how each layer of the system must be carefully designed to prevent both data corruption and resource waste."*

---

## Project Context
- **Backend**: FastAPI with OpenAI Responses API
- **LLM**: gpt-4o-mini with few-shot learning
- **Databases**: DuckDB (SQL warehouse), Qdrant (vector search)
- **Key Files Modified**:
  - `api/services/chat_service.py` (main orchestration)
  - `embeddings/query.py` (vector retrieval)
  - `data/golden_sql.json` (few-shot examples)
