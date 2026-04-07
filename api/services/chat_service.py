from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from typing import Any

from openai import OpenAI

from api.observability import get_request_id
from api.services.schema_context import (
    build_sql_tool_definition,
    get_schema_catalog,
    get_specific_schema_context,
)
from api.services.table_selector import select_tables_for_query
from api.services.sql_service import run_sql_query
from api.services.vector_service import run_vector_search
from embeddings.config import load_settings

LOGGER = logging.getLogger(__name__)




SYSTEM_PROMPT = """
You are PulseIQ, an analytics and support intelligence assistant for a synthetic e-commerce business with product, order, refund, event, and support-ticket data.

## Objective
Answer the user's question using the available tools and only the evidence returned by those tools.
If the evidence is weak or missing, say that there is insufficient evidence.

## Tool selection
Use `run_sql_query` for:
- metrics
- rankings
- trends
- calculations
- warehouse serving-table lookups

Use `run_vector_search` for:
- what customers are saying
- complaint themes
- semantic support-ticket evidence
- quotes or examples from ticket text

Use both tools when the question mixes structured metrics with customer language.

## Grounding rules
- Numeric claims must come from SQL evidence.
- Complaint themes or customer language must come from vector-search evidence.
- Do not claim a complaint theme for a product or region unless the retrieved ticket evidence matches that same product or region.
- Do not infer legal, compliance, regulatory, safety, or fraud violations from generic risk scores or complaint counts.
- If the user asks for that kind of claim and the ticket evidence does not explicitly support it, answer that there is insufficient evidence.
- When displaying products or business entities in results, **always show human-readable names** (product_name, region, customer_name) instead of IDs—unless explicitly asked for schema reference or table-join documentation.

## Interpretation rules
- Resolve ambiguous business questions by choosing the most standard warehouse metric available and state the metric clearly in the answer.
- Prefer serving tables whose grain matches the question:
  - `mart_product_sales` for product-level sales rankings and refund performance
  - `mart_region_customer_health` for region-level commercial and support health
  - `mart_product_risk` for product risk and operational health
  - `mart_product_engagement_daily` for product engagement and conversion
  - `mart_support_issue_trends` for issue-type support trends
- For recent-period questions, use DuckDB date filters such as `metric_date >= current_date - interval '30 days'` or the equivalent real date column for that table.

## Output contract
- Be concise by default: usually 3-5 bullets or under 180 words unless the user explicitly asks for detail.
- Use proper Markdown lists.
- Put each bullet or numbered item on its own line.
- If evidence is mixed, separate the structured signal from the customer-evidence signal clearly.
- When a claim cannot be grounded, say so directly instead of guessing.

## SQL constraints
## DuckDB SQL rules
- Use only `SELECT` queries.
- Do not use `DATE_SUB(...)`.
- Do not invent placeholder variables like `threshold_value`.
- When grouping, every selected non-aggregated column must be included in `GROUP BY`.
- For questions about customer language, do not use SQL alone when vector evidence is needed.
- When expected metric columns are NULL or return zero results, respond that "data is unavailable" rather than inferring reasons or providing default values.
""".strip()

VECTOR_TOOL = {
    "type": "function",
    "name": "run_vector_search",
    "description": "Semantic retrieval over support-ticket chunks with optional metadata filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "query_text": {"type": "string"},
            "limit": {"type": "integer", "default": 3, "maximum": 3},
            "filters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "category": {"type": "string"},
                    "issue_type": {"type": "string"},
                    "priority": {"type": "string"},
                    "region": {"type": "string"},
                    "segment": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        "required": ["query_text"],
        "additionalProperties": False,
    },
}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def _json_dumps(value: Any) -> str:
    return json.dumps(_json_safe(value))


def _needs_vector_only(question: str) -> bool:
    q = question.lower()
    return any(
        term in q
        for term in [
            "legal",
            "compliance",
            "regulatory",
            "violation",
            "violating",
            "fraud",
            "fraudulent",
            "consumer safety law",
            "safety law",
        ]
    )


def _needs_customer_voice(question: str) -> bool:
    q = question.lower()
    return any(
        term in q
        for term in [
            "what are customers saying",
            "customers actually saying",
            "customer pain",
            "complaint themes",
            "back that up",
            "describe those experiences",
            "unhappy",
            "something else",
            "themes",
            "voice",
            "customers saying",
            "complaints",
            "customer complaints",
        ]
    )


def _needs_structured_context(question: str) -> bool:
    q = question.lower()
    return any(
        term in q
        for term in [
            "risk",
            "refund",
            "csat",
            "operational",
            "recently",
            "last 30 days",
            "lately",
            "highest",
            "lowest",
            "changed",
            "support page views",
            "resolve",
            "operational picture",
            "going wrong",
            "getting people nervous",
        ]
    )


def _needs_hybrid(question: str) -> bool:
    q = question.lower()
    if any(
        term in q
        for term in [
            "what seems to be going wrong",
            "current operational picture",
            "operational picture",
            "operationally fragile",
            "getting people nervous",
        ]
    ):
        return True
    return _needs_customer_voice(question) and _needs_structured_context(question)


def _needs_product_filtered_search(question: str) -> bool:
    """Check if this is a product-specific hybrid question requiring filtered vector searches."""
    q = question.lower()
    return any(
        term in q
        for term in ["csat", "refund", "complaint", "unhappy", "issue with"]
    ) and _needs_hybrid(question)


def _summarize_evidence(evidence: list[dict[str, Any]], max_items: int = 3) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []

    for item in evidence:
        tool = item["tool"]
        result = item["result"]
        if tool == "run_sql_query":
            rows = _json_safe(result[:max_items])
            summary.append({"tool": tool, "rows": rows, "row_count": len(result)})
        elif tool == "run_vector_search":
            matches = [
                {
                    "ticket_id": match.get("ticket_id"),
                    "product_name": match.get("product_name"),
                    "issue_type": match.get("issue_type"),
                    "priority": match.get("priority"),
                "created_date": match.get("created_date"),
                "region": match.get("region"),
                "text": match.get("text"),
                "score": round(float(match.get("score", 0)), 4),
            }
                for match in result[:max_items]
            ]
            summary.append({"tool": tool, "matches": matches, "match_count": len(result)})

        if len(summary) >= max_items:
            break

    return summary


def _tool_result_for_model(tool: str, result: list[dict[str, Any]], max_items: int = 3) -> dict[str, Any]:
    if tool == "run_sql_query":
        return {
            "tool": tool,
            "row_count": len(result),
            "rows": _json_safe(result[:max_items]),
        }
    if tool == "run_vector_search":
        matches = [
            {
                "ticket_id": item.get("ticket_id"),
                "product_name": item.get("product_name"),
                "issue_type": item.get("issue_type"),
                "priority": item.get("priority"),
                "created_date": item.get("created_date"),
                "region": item.get("region"),
                "text": item.get("text"),
                "score": round(float(item.get("score", 0)), 4),
            }
            for item in result[:max_items]
        ]
        return {
            "tool": tool,
            "match_count": len(result),
            "matches": matches,
        }
    return {"tool": tool, "result_count": len(result)}


def _should_add_vector_evidence(evidence: list[dict[str, Any]], product_id_filter: str | None) -> bool:
    """
    Check if this vector search result would be a duplicate based on product_id.
    Returns True if we should add it (no duplicate), False if it's a duplicate to skip.
    """
    if not product_id_filter:
        # No product filter means it's a different type of search (generic)
        # These are always added as they're not product-specific
        return True
    
    # Check if this product_id already has vector evidence
    existing_product_ids = {
        str(match.get("product_id"))
        for item in evidence
        if item["tool"] == "run_vector_search"
        for match in item["result"]
        if match.get("product_id")
    }
    
    return str(product_id_filter) not in existing_product_ids


def _route_from_tools(tools_used: set[str]) -> str:
    if tools_used == {"run_sql_query"}:
        return "sql"
    if tools_used == {"run_vector_search"}:
        return "vector"
    if tools_used == {"run_sql_query", "run_vector_search"}:
        return "hybrid"
    return "unknown"


def _question_guidance(question: str) -> str:
    q = question.lower()
    guidance: list[str] = []

    unsupported_claim_terms = ["legal", "compliance", "regulatory", "violation", "fraud"]
    if any(term in q for term in unsupported_claim_terms):
        guidance.append(
            "Do not infer legal/compliance/regulatory violations from generic complaints or risk scores. "
            "Use run_vector_search first, and if the retrieved evidence does not explicitly mention such violations, answer that there is insufficient evidence."
        )
    
    if _needs_product_filtered_search(question):
        guidance.append(
            "This question requires matching customer feedback to specific products. "
            "When using run_vector_search, include product_id filters to retrieve tickets for the products identified in your SQL results. "
            "Do NOT make generic unfiltered vector searches—only search for evidence tied to specific products."
        )
    elif _needs_hybrid(question):
        guidance.append(
            "This question mixes structured business signals with customer-language evidence, so use both tools and keep the final answer grounded."
        )
    elif _needs_customer_voice(question):
        guidance.append(
            "This question is primarily about customer language or complaint themes, so prefer run_vector_search."
        )

    return "\n".join(guidance)


def _tool_policy_for_question(question: str) -> dict[str, Any]:
    """
    Determine which tools should be exposed for this request.

    Production policy:
    - Fail-safe for ambiguity: expose both tools (hybrid) when unclear.
    - Restrict aggressively only for high-confidence routing signals.
    """
    is_vector_only = _needs_vector_only(question)
    is_hybrid = _needs_hybrid(question)
    needs_customer_voice = _needs_customer_voice(question)
    needs_structured = _needs_structured_context(question)

    if is_vector_only:
        return {"enable_sql": False, "enable_vector": True, "mode": "vector_only"}
    if is_hybrid:
        return {"enable_sql": True, "enable_vector": True, "mode": "hybrid"}
    if needs_customer_voice and not needs_structured:
        return {"enable_sql": False, "enable_vector": True, "mode": "vector_only"}
    if needs_structured and not needs_customer_voice:
        return {"enable_sql": True, "enable_vector": False, "mode": "sql_only"}
    return {"enable_sql": True, "enable_vector": True, "mode": "hybrid_fallback"}


def _log_tool_policy_event(
    *,
    request_id: str,
    tool_policy_mode: str,
    tools_exposed: list[str],
    route_final: str,
    latency_ms: int,
    token_usage: dict[str, int],
    tool_errors_count: int,
    grounding_passed: bool | None = None,
    grounding_violations_count: int | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": "chat_request_completed",
        "request_id": request_id,
        "tool_policy_mode": tool_policy_mode,
        "tools_exposed": tools_exposed,
        "route_final": route_final,
        "latency_ms": latency_ms,
        "token_usage": token_usage,
        "tool_errors_count": tool_errors_count,
    }
    if grounding_passed is not None:
        payload["grounding_passed"] = grounding_passed
    if grounding_violations_count is not None:
        payload["grounding_violations_count"] = grounding_violations_count

    LOGGER.info(
        json.dumps(
            payload,
            default=str,
        )
    )


_NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?%?")


def _extract_sql_and_vector_evidence(evidence: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sql_rows: list[dict[str, Any]] = []
    vector_matches: list[dict[str, Any]] = []
    for item in evidence:
        if item.get("tool") == "run_sql_query":
            sql_rows.extend(item.get("result", []))
        elif item.get("tool") == "run_vector_search":
            vector_matches.extend(item.get("result", []))
    return sql_rows, vector_matches


def _supported_numeric_values(sql_rows: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for row in sql_rows:
        for v in row.values():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                values.append(float(v))
    return values


def _evaluate_grounding(answer_text: str, route: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Deterministic grounding checks (fast, production-safe):
    - Numeric claims must be backed by SQL evidence.
    - Hybrid entity references should align with SQL/vector entity overlap.
    """
    sql_rows, vector_matches = _extract_sql_and_vector_evidence(evidence)
    violations: list[str] = []
    violation_types: list[str] = []

    if route in {"sql", "hybrid"}:
        if not sql_rows and _NUMBER_RE.search(answer_text):
            violations.append("Answer contains numeric claims but no SQL evidence rows are available.")
            violation_types.append("numeric_without_sql_evidence")
        elif sql_rows:
            supported = _supported_numeric_values(sql_rows)
            if supported:
                unsupported_numeric_count = 0
                for match in _NUMBER_RE.finditer(answer_text):
                    token = match.group(0).strip()
                    is_percent = token.endswith("%")
                    token_num = token[:-1] if is_percent else token
                    try:
                        parsed = float(token_num)
                    except ValueError:
                        continue
                    # Ignore list numbering / small ordinal-like values in prose.
                    if parsed.is_integer() and 0 <= parsed <= 10:
                        continue
                    # Ignore likely years.
                    if parsed.is_integer() and 1900 <= parsed <= 2100:
                        continue

                    candidates = [parsed]
                    if is_percent:
                        candidates.append(parsed / 100.0)

                    has_match = False
                    for c in candidates:
                        if any(abs(c - s) <= 0.01 for s in supported):
                            has_match = True
                            break
                    if not has_match:
                        unsupported_numeric_count += 1
                        if unsupported_numeric_count >= 3:
                            break

                if unsupported_numeric_count >= 3:
                    violations.append("Multiple numeric claims in the answer could not be reconciled with SQL evidence values.")
                    violation_types.append("numeric_mismatch")

    if route == "hybrid" and sql_rows and vector_matches:
        sql_products = {
            str(row.get("product_name", "")).strip().lower()
            for row in sql_rows
            if row.get("product_name")
        }
        vector_products = {
            str(match.get("product_name", "")).strip().lower()
            for match in vector_matches
            if match.get("product_name")
        }
        if sql_products and vector_products and not (sql_products & vector_products):
            violations.append("Hybrid evidence contains no overlapping product entities between SQL and vector results.")
            violation_types.append("hybrid_entity_mismatch")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "violation_types": violation_types,
    }


def _apply_grounding_guardrail(answer_text: str, route: str, evidence: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    report = _evaluate_grounding(answer_text=answer_text, route=route, evidence=evidence)
    strict = os.environ.get("GROUNDING_GUARDRAIL_STRICT", "1").strip() not in {"0", "false", "False"}
    if strict and not report["passed"]:
        guarded = (
            "I could not fully ground the final answer to the retrieved evidence. "
            "There is insufficient evidence to answer this reliably."
        )
        return guarded, report
    return answer_text, report


def _normalize_answer_format(text: str) -> str:
    normalized = text.replace("\r\n", "\n").strip()
    replacements = [
        ("• ", "\n- "),
        (" - ", "\n- "),
        (" 1. ", "\n1. "),
        (" 2. ", "\n2. "),
        (" 3. ", "\n3. "),
        (" 4. ", "\n4. "),
        (" 5. ", "\n5. "),
    ]
    for source, target in replacements:
        normalized = normalized.replace(source, target)

    lines = [line.rstrip() for line in normalized.split("\n")]
    cleaned: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and previous_blank:
            continue
        cleaned.append(line)
        previous_blank = is_blank
    return "\n".join(cleaned).strip()


def _compose_grounded_answer(question: str, route: str, evidence: list[dict[str, Any]], raw_answer: str) -> str:
    q = question.lower()
    if route != "hybrid":
        return _normalize_answer_format(raw_answer)

    sql_rows: list[dict[str, Any]] = []
    vector_matches: list[dict[str, Any]] = []
    for item in evidence:
        if item["tool"] == "run_sql_query":
            sql_rows.extend(item["result"])
        elif item["tool"] == "run_vector_search":
            vector_matches.extend(item["result"])

    if not sql_rows or not vector_matches:
        return _normalize_answer_format(raw_answer)

    top_rows = [row for row in sql_rows if row.get("product_id") and row.get("product_name")][:3]
    if not top_rows:
        return _normalize_answer_format(raw_answer)

    matches_by_product: dict[str, list[dict[str, Any]]] = {}
    for match in vector_matches:
        product_id = match.get("product_id")
        if not product_id:
            continue
        matches_by_product.setdefault(str(product_id), []).append(match)

    lines: list[str] = []
    if "refund" in q:
        lines.append("## Highest-refund products")
    elif "csat" in q:
        lines.append("## Lowest-CSAT products")
    elif "risk" in q or "operational" in q or "going wrong" in q or "nervous" in q:
        lines.append("## Products with the strongest risk signals")

    if lines:
        for idx, row in enumerate(top_rows, start=1):
            details: list[str] = []
            if "refund" in q and row.get("refund_rate") is not None:
                details.append(f"refund rate {row['refund_rate']}")
            if "csat" in q and row.get("avg_csat_score") is not None:
                details.append(f"avg CSAT {row['avg_csat_score']}")
            if row.get("risk_score") is not None and ("risk" in q or "operational" in q or "going wrong" in q or "nervous" in q):
                details.append(f"risk score {row['risk_score']}")
            if details:
                lines.append(f"{idx}. {row['product_name']} — {', '.join(details)}")
            else:
                lines.append(f"{idx}. {row['product_name']}")
        lines.append("")

    lines.append("## Customer complaint evidence")
    
    # Filter vector matches to ONLY those matching the top SQL products
    allowed_product_ids = {str(row.get("product_id")) for row in top_rows if row.get("product_id")}
    filtered_matches_by_product: dict[str, list[dict[str, Any]]] = {}
    for product_id, matches in matches_by_product.items():
        if str(product_id) in allowed_product_ids:
            filtered_matches_by_product[str(product_id)] = matches
    
    # Show evidence only for products in the top results
    for row in top_rows:
        product_id = str(row.get("product_id", ""))
        product_name = str(row["product_name"])
        
        if not product_id:
            lines.append(f"- **{product_name}**")
            lines.append("  - Product ID not available for matching customer feedback.")
            continue
        
        matches = filtered_matches_by_product.get(product_id, [])[:2]
        if matches:
            issue_types = ", ".join(
                sorted({str(match.get("issue_type", "unknown issue")) for match in matches})
            )
            lines.append(f"- **{product_name}**")
            lines.append(f"  - Main themes: {issue_types}")
            
            # Deduplicate at text level to avoid showing identical complaints twice
            seen_texts = set()
            for match in matches:
                text = str(match.get("text", "")).strip()
                if text and text not in seen_texts:
                    lines.append(f'  - Example: "{text}"')
                    seen_texts.add(text)
        else:
            lines.append(f"- **{product_name}**")
            if "refund" in q or "unhappy" in q:
                lines.append("  - No customer complaints retrieved for this product.")
            elif "csat" in q or "saying" in q:
                lines.append("  - No customer feedback retrieved for this product.")
            else:
                lines.append("  - No customer feedback retrieved for this product.")

    lines.append("")
    lines.append("## Takeaway")
    if "refund" in q or "risk" in q or "operational" in q or "going wrong" in q or "nervous" in q:
        lines.append("- Focus remediation efforts on the highest-risk products first—they represent the biggest operational and customer satisfaction threats.")
        lines.append("- Use the complaint evidence to understand root causes (quality, returns, defects) and prioritize fixes accordingly.")
    elif "csat" in q:
        lines.append("- These products are driving customer dissatisfaction—investigate and resolve the primary complaint themes.")
        lines.append("- Customer quotes show the actual pain points; address the underlying issues to improve scores.")
    else:
        lines.append("- Focus on the products showing the strongest signals in your query criteria.")
        lines.append("- Pair quantitative metrics with customer feedback to understand 'why' behind the numbers.")

    return "\n".join(lines).strip()


def _top_sql_rows_for_hybrid(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sql_rows: list[dict[str, Any]] = []
    for item in evidence:
        if item["tool"] == "run_sql_query":
            sql_rows.extend(item["result"])
    return [row for row in sql_rows if row.get("product_id") and row.get("product_name")][:3]


def _top_region_rows_for_hybrid(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sql_rows: list[dict[str, Any]] = []
    for item in evidence:
        if item["tool"] == "run_sql_query":
            sql_rows.extend(item["result"])
    return [row for row in sql_rows if row.get("region")][:2]


def _supplement_hybrid_vector_evidence(
    question: str,
    evidence: list[dict[str, Any]],
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    top_rows = _top_sql_rows_for_hybrid(evidence)

    existing_product_ids = {
        str(match.get("product_id"))
        for item in evidence
        if item["tool"] == "run_vector_search"
        for match in item["result"]
        if match.get("product_id")
    }

    query_text = question
    if "refund" in question.lower():
        query_text = f"{question} customer unhappy refund complaint"
    elif "csat" in question.lower():
        query_text = f"{question} what customers are saying"

    for row in top_rows:
        product_id = str(row["product_id"])
        if product_id in existing_product_ids:
            continue
        refined = run_vector_search(
            query_text=query_text,
            qdrant_path=settings["qdrant_path"],
            collection_name=settings["collection_name"],
            embedding_model=settings["embedding_model"],
            limit=2,
            filters={"product_id": product_id},
        )
        if refined:
            evidence.append({"tool": "run_vector_search", "result": refined})

    if top_rows:
        return evidence

    top_regions = _top_region_rows_for_hybrid(evidence)
    existing_regions = {
        str(match.get("region"))
        for item in evidence
        if item["tool"] == "run_vector_search"
        for match in item["result"]
        if match.get("region")
    }
    for row in top_regions:
        region = str(row["region"])
        if region in existing_regions:
            continue
        refined = run_vector_search(
            query_text=f"{question} customer complaints in {region}",
            qdrant_path=settings["qdrant_path"],
            collection_name=settings["collection_name"],
            embedding_model=settings["embedding_model"],
            limit=2,
            filters={"region": region},
        )
        if refined:
            evidence.append({"tool": "run_vector_search", "result": refined})

    return evidence


def answer_question(question: str, debug: bool = False) -> dict[str, Any]:
    request_id = get_request_id() or str(uuid.uuid4())
    started_at = time.perf_counter()
    token_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }

    settings = load_settings()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for chat answers.")

    client = OpenAI(api_key=api_key, timeout=45.0, max_retries=1)
    model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")

    # ==========================================
    # 1. Dynamic Tool Policy + SQL Routing
    # ==========================================
    tool_policy = _tool_policy_for_question(question)
    selected_table_names: list[str] = []
    schema_context: dict[str, Any] = {"allowed_table_names": [], "prompt_block": ""}
    allowed_table_names: list[str] = []
    sql_tool: dict[str, Any] | None = None

    if tool_policy["enable_sql"]:
        selected_table_names = select_tables_for_query(question)

        # Safety fallback: if router returns nothing but SQL is enabled,
        # expose all known serving/dimension tables instead of hard-failing.
        if not selected_table_names:
            selected_table_names = list(get_schema_catalog().keys())

        schema_context = get_specific_schema_context(selected_table_names)
        allowed_table_names = schema_context.get("allowed_table_names", [])
        if allowed_table_names:
            sql_tool = build_sql_tool_definition(allowed_table_names)
        else:
            # If no allowlist can be established, disable SQL tool for safety.
            tool_policy["enable_sql"] = False
    
    # ==========================================
    # 2. NEW STEP: Golden SQL Retrieval (Few-Shot)
    # ==========================================
    golden_sql_prompt = ""
    should_retrieve_golden_sql = tool_policy["enable_sql"] and bool(selected_table_names) and (
        _needs_structured_context(question) or _needs_hybrid(question)
    )

    if should_retrieve_golden_sql:
        try:
            golden_matches = run_vector_search(
                query_text=question,
                qdrant_path=settings["qdrant_path"],
                collection_name="sql_examples",  # Querying our new seed data
                embedding_model=settings["embedding_model"],
                limit=3,
            )

            if golden_matches:
                example_lines = [
                    "## ⚠️ GOLDEN SQL REFERENCE - USE EXACT CODE BELOW",
                    "🚨 CRITICAL: When a user's question matches one of these, copy the SQL code EXACTLY as shown.",
                    "Do NOT rewrite, do NOT join tables differently, do NOT change aliases or date logic.",
                    "Copy line-for-line unless the user explicitly requests a different timeframe or limit.",
                    "",
                ]
                for idx, match in enumerate(golden_matches, start=1):
                    # Extract the payload fields we seeded
                    q = match.get("question")
                    sql = match.get("sql")
                    if q and sql:
                        example_lines.append(f"### Example {idx}")
                        example_lines.append(f"User asks: {q}")
                        example_lines.append("Use this SQL exactly:")
                        example_lines.append("```sql")
                        example_lines.append(sql)
                        example_lines.append("```")
                        example_lines.append("")

                golden_sql_prompt = "\n".join(example_lines).strip()

        except Exception as exc:
            # Fail gracefully if the collection isn't seeded yet
            if debug:
                print(f"Golden SQL Retrieval failed: {exc}")

    # ==========================================
    # 3. Construct the LLM Prompt
    # ==========================================
    dynamic_guidance = _question_guidance(question)
    
    input_items: list[dict[str, Any]] = [
        {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
    ]

    if tool_policy["enable_sql"] and schema_context.get("prompt_block"):
        input_items.append(
            {"role": "system", "content": [{"type": "input_text", "text": schema_context["prompt_block"]}]}
        )
    
    # Inject the Golden SQL examples if we successfully retrieved them
    if golden_sql_prompt:
        input_items.append(
            {"role": "system", "content": [{"type": "input_text", "text": golden_sql_prompt}]}
        )
        
    if dynamic_guidance:
        input_items.append(
            {"role": "system", "content": [{"type": "input_text", "text": dynamic_guidance}]}
        )
        
    input_items.append(
        {"role": "user", "content": [{"type": "input_text", "text": question}]}
    )

    tools_for_model: list[dict[str, Any]] = []
    if tool_policy["enable_sql"] and sql_tool is not None:
        tools_for_model.append(sql_tool)
    if tool_policy["enable_vector"]:
        tools_for_model.append(VECTOR_TOOL)
    if not tools_for_model:
        # Final defensive fallback: always expose semantic retrieval.
        tools_for_model.append(VECTOR_TOOL)
    tools_exposed = [str(tool.get("name", "unknown")) for tool in tools_for_model]
    
    evidence: list[dict[str, Any]] = []
    tools_used: set[str] = set()
    tool_errors: list[dict[str, str]] = []
    tool_rejections = 0
    max_tool_errors = 3
    max_rounds = 6
    supplementary_search_done = False

    for _ in range(max_rounds):
        response = client.responses.create(
            model=model,
            input=input_items,
            tools=tools_for_model,
        )
        usage = getattr(response, "usage", None)
        if usage is not None:
            token_usage["input_tokens"] += int(getattr(usage, "input_tokens", 0) or 0)
            token_usage["output_tokens"] += int(getattr(usage, "output_tokens", 0) or 0)
            token_usage["total_tokens"] += int(getattr(usage, "total_tokens", 0) or 0)

        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            route = _route_from_tools(tools_used)
            if route == "hybrid" and not supplementary_search_done:
                evidence = _supplement_hybrid_vector_evidence(question, evidence, settings)
                supplementary_search_done = True
                route = _route_from_tools(tools_used)
            answer_text = _compose_grounded_answer(
                question=question,
                route=route,
                evidence=evidence,
                raw_answer=response.output_text or "I could not produce an answer.",
            )
            answer_text, grounding_report = _apply_grounding_guardrail(
                answer_text=answer_text,
                route=route,
                evidence=evidence,
            )
            summarized_evidence = _summarize_evidence(evidence)
            debug_payload = (
                {
                    "raw_evidence": evidence,
                    "grounding": grounding_report,
                }
                if debug
                else None
            )
            _log_tool_policy_event(
                request_id=request_id,
                tool_policy_mode=str(tool_policy["mode"]),
                tools_exposed=tools_exposed,
                route_final=route,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                token_usage=token_usage,
                tool_errors_count=len(tool_errors),
                grounding_passed=bool(grounding_report.get("passed")),
                grounding_violations_count=len(grounding_report.get("violations", [])),
            )
            return {
                "answer": answer_text,
                "route": route,
                "evidence": summarized_evidence,
                "debug": debug_payload,
            }

        input_items.extend(response.output)
        for call in function_calls:
            arguments = json.loads(call.arguments)
            if call.name == "run_sql_query":
                if _needs_vector_only(question):
                    tool_rejections += 1
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": _json_dumps(
                                {
                                    "tool": call.name,
                                    "error": "This question requires semantic evidence, not SQL-only inference.",
                                    "hint": (
                                        "For legal, compliance, safety, or fraud claims, do not use SQL risk scores alone. "
                                        "Use run_vector_search, and if no explicit evidence appears, answer that there is insufficient evidence."
                                    ),
                                }
                            ),
                        }
                    )
                    if tool_rejections >= max_tool_errors:
                        route = "vector"
                        _log_tool_policy_event(
                            request_id=request_id,
                            tool_policy_mode=str(tool_policy["mode"]),
                            tools_exposed=tools_exposed,
                            route_final=route,
                            latency_ms=int((time.perf_counter() - started_at) * 1000),
                            token_usage=token_usage,
                            tool_errors_count=len(tool_errors),
                        )
                        return {
                            "answer": "There is insufficient evidence to make that legal, safety, or fraud claim from the available support-ticket evidence.",
                            "route": route,
                            "evidence": _summarize_evidence(evidence),
                            "debug": {"raw_evidence": evidence, "tool_errors": tool_errors} if debug else None,
                        }
                    continue
                try:
                    result = run_sql_query(
                        settings["duckdb_path"],
                        arguments["sql"],
                        allowed_table_names=allowed_table_names,
                    )
                except Exception as exc:
                    tool_errors.append({"tool": call.name, "error": str(exc)})
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": _json_dumps(
                                {
                                    "tool": call.name,
                                    "error": str(exc),
                                    "hint": (
                                        "Correct the SQL using the exact schema above. "
                                        "If product_name is needed for support issues, use "
                                        "fct_support_tickets_enriched or join dim_products on product_id. "
                                        "If evidence is not available, say insufficient evidence."
                                    ),
                                }
                            ),
                        }
                    )
                    if len(tool_errors) >= max_tool_errors:
                        summarized_evidence = _summarize_evidence(evidence)
                        route = _route_from_tools(tools_used)
                        debug_payload = {"raw_evidence": evidence, "tool_errors": tool_errors} if debug else None
                        _log_tool_policy_event(
                            request_id=request_id,
                            tool_policy_mode=str(tool_policy["mode"]),
                            tools_exposed=tools_exposed,
                            route_final=route,
                            latency_ms=int((time.perf_counter() - started_at) * 1000),
                            token_usage=token_usage,
                            tool_errors_count=len(tool_errors),
                        )
                        return {
                            "answer": "I could not complete the request reliably with the available tool outputs. There is insufficient evidence or the generated query needs correction.",
                            "route": route,
                            "evidence": summarized_evidence,
                            "debug": debug_payload,
                        }
                    continue
            elif call.name == "run_vector_search":
                # Optimization: Reject unfiltered searches for product-specific questions
                if _needs_product_filtered_search(question):
                    filters = arguments.get("filters", {})
                    product_id_filter = filters.get("product_id") if filters else None
                    
                    if not product_id_filter:
                        # No product filter - reject and ask LLM to add it
                        input_items.append(
                            {
                                "type": "function_call_output",
                                "call_id": call.call_id,
                                "output": _json_dumps(
                                    {
                                        "tool": call.name,
                                        "error": "Generic unfiltered search not allowed for this question type.",
                                        "hint": "For questions about specific product metrics mixed with customer feedback, use product_id filters. Retrieve tickets only for the product IDs found in your SQL results.",
                                    }
                                ),
                            }
                        )
                        continue
                
                try:
                    result = run_vector_search(
                        query_text=arguments["query_text"],
                        qdrant_path=settings["qdrant_path"],
                        collection_name=settings["collection_name"],
                        embedding_model=settings["embedding_model"],
                        limit=arguments.get("limit", 5),
                        filters=arguments.get("filters"),
                    )
                except Exception as exc:
                    tool_errors.append({"tool": call.name, "error": str(exc)})
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": _json_dumps(
                                {
                                    "tool": call.name,
                                    "error": str(exc),
                                    "hint": "Adjust the query or filters. If evidence is not available, say insufficient evidence.",
                                }
                            ),
                        }
                    )
                    if len(tool_errors) >= max_tool_errors:
                        summarized_evidence = _summarize_evidence(evidence)
                        route = _route_from_tools(tools_used)
                        debug_payload = {"raw_evidence": evidence, "tool_errors": tool_errors} if debug else None
                        _log_tool_policy_event(
                            request_id=request_id,
                            tool_policy_mode=str(tool_policy["mode"]),
                            tools_exposed=tools_exposed,
                            route_final=route,
                            latency_ms=int((time.perf_counter() - started_at) * 1000),
                            token_usage=token_usage,
                            tool_errors_count=len(tool_errors),
                        )
                        return {
                            "answer": "I could not complete the request reliably with the available tool outputs. There is insufficient evidence or the retrieval needs correction.",
                            "route": route,
                            "evidence": summarized_evidence,
                            "debug": debug_payload,
                        }
                    continue
            else:
                raise ValueError(f"Unsupported tool call: {call.name}")

            tools_used.add(call.name)
            
            # For vector searches with product filters, check for duplicates
            if call.name == "run_vector_search":
                filters = arguments.get("filters", {})
                product_id_filter = filters.get("product_id") if filters else None
                
                if _should_add_vector_evidence(evidence, product_id_filter):
                    evidence.append({"tool": call.name, "result": result})
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": _json_dumps(_tool_result_for_model(call.name, result)),
                        }
                    )
                else:
                    # Skip duplicate - tell LLM this product already has vector evidence
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": _json_dumps({
                                "tool": call.name,
                                "error": "Product already has vector evidence. Skipping duplicate search.",
                                "match_count": 0,
                                "matches": [],
                            }),
                        }
                    )
            else:
                evidence.append({"tool": call.name, "result": result})
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": _json_dumps(_tool_result_for_model(call.name, result)),
                    }
                )

        route = _route_from_tools(tools_used)
        if route == "sql" and _needs_hybrid(question) and not supplementary_search_done:
            evidence = _supplement_hybrid_vector_evidence(question, evidence, settings)
            supplementary_search_done = True
            if any(item["tool"] == "run_vector_search" for item in evidence):
                tools_used.add("run_vector_search")

    route = _route_from_tools(tools_used)
    if route == "hybrid" and not supplementary_search_done:
        evidence = _supplement_hybrid_vector_evidence(question, evidence, settings)
        supplementary_search_done = True
        route = _route_from_tools(tools_used)

    summarized_evidence = _summarize_evidence(evidence)
    debug_payload = {
        "raw_evidence": evidence,
        "tool_errors": tool_errors,
        "timeout_reason": "max_tool_rounds_exceeded",
    } if debug else None

    if evidence:
        fallback_answer = _compose_grounded_answer(
            question=question,
            route=route,
            evidence=evidence,
            raw_answer="I gathered evidence, but the tool loop did not converge cleanly. Here is the grounded summary from the evidence I was able to collect.",
        )
        fallback_answer, grounding_report = _apply_grounding_guardrail(
            answer_text=fallback_answer,
            route=route,
            evidence=evidence,
        )
        if debug_payload is not None:
            debug_payload["grounding"] = grounding_report

        _log_tool_policy_event(
            request_id=request_id,
            tool_policy_mode=str(tool_policy["mode"]),
            tools_exposed=tools_exposed,
            route_final=route,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            token_usage=token_usage,
            tool_errors_count=len(tool_errors),
            grounding_passed=bool(grounding_report.get("passed")),
            grounding_violations_count=len(grounding_report.get("violations", [])),
        )
        return {
            "answer": fallback_answer,
            "route": route,
            "evidence": summarized_evidence,
            "debug": debug_payload,
        }

    _log_tool_policy_event(
        request_id=request_id,
        tool_policy_mode=str(tool_policy["mode"]),
        tools_exposed=tools_exposed,
        route_final=route,
        latency_ms=int((time.perf_counter() - started_at) * 1000),
        token_usage=token_usage,
        tool_errors_count=len(tool_errors),
    )
    return {
        "answer": "I could not complete the request reliably because the retrieval loop did not finish cleanly. Please try again or narrow the question slightly.",
        "route": route,
        "evidence": summarized_evidence,
        "debug": debug_payload,
    }
