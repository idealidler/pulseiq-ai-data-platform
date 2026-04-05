from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from api.services.schema_context import build_sql_tool_definition, get_assistant_schema_context
from api.services.sql_service import run_sql_query
from api.services.vector_service import run_vector_search
from embeddings.config import load_settings


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
""".strip()

VECTOR_TOOL = {
    "type": "function",
    "name": "run_vector_search",
    "description": "Semantic retrieval over support-ticket chunks with optional metadata filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "query_text": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
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
    if _needs_hybrid(question):
        guidance.append(
            "This question mixes structured business signals with customer-language evidence, so use both tools and keep the final answer grounded."
        )
    elif _needs_customer_voice(question):
        guidance.append(
            "This question is primarily about customer language or complaint themes, so prefer run_vector_search."
        )

    return "\n".join(guidance)


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
    for row in top_rows:
        product_id = str(row["product_id"])
        product_name = str(row["product_name"])
        matches = matches_by_product.get(product_id, [])[:2]
        if matches:
            issue_types = ", ".join(
                sorted({str(match.get("issue_type", "unknown issue")) for match in matches})
            )
            lines.append(f"- **{product_name}**")
            lines.append(f"  - Main themes: {issue_types}")
            for match in matches:
                text = str(match.get("text", "")).strip()
                if text:
                    lines.append(f'  - Example: "{text}"')
        else:
            lines.append(f"- **{product_name}**")
            if "refund" in q or "unhappy" in q:
                lines.append("  - No same-product ticket snippet was retrieved, so I cannot confidently explain why customers are unhappy from ticket text alone.")
            elif "csat" in q or "saying" in q:
                lines.append("  - No same-product ticket snippet was retrieved, so I cannot quote what customers are saying for this product yet.")
            else:
                lines.append("  - No same-product customer pain snippet was retrieved in the top evidence set.")

    lines.append("")
    lines.append("## Takeaway")
    if "refund" in q:
        lines.append("- Refund ranking comes from structured warehouse metrics, while customer unhappiness should be grounded in same-product ticket evidence.")
    elif "csat" in q:
        lines.append("- CSAT ranking comes from structured support data, while what customers are saying should be grounded in same-product ticket evidence.")
    else:
        lines.append("- Structured warehouse signals show which products look riskiest operationally.")
    lines.append("- Complaint evidence is shown only when a retrieved support-ticket snippet matches the same product.")

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
    settings = load_settings()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for chat answers.")

    client = OpenAI(api_key=api_key, timeout=45.0, max_retries=1)
    model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
    dynamic_guidance = _question_guidance(question)
    schema_context = get_assistant_schema_context()
    sql_tool = build_sql_tool_definition()
    input_items: list[dict[str, Any]] = [
        {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
        {"role": "system", "content": [{"type": "input_text", "text": schema_context["prompt_block"]}]},
        *(
            [{"role": "system", "content": [{"type": "input_text", "text": dynamic_guidance}]}]
            if dynamic_guidance
            else []
        ),
        {"role": "user", "content": [{"type": "input_text", "text": question}]},
    ]
    evidence: list[dict[str, Any]] = []
    tools_used: set[str] = set()
    tool_errors: list[dict[str, str]] = []
    tool_rejections = 0
    max_tool_errors = 3
    max_rounds = 6

    for _ in range(max_rounds):
        response = client.responses.create(
            model=model,
            input=input_items,
            tools=[sql_tool, VECTOR_TOOL],
        )

        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            route = _route_from_tools(tools_used)
            if route == "hybrid":
                evidence = _supplement_hybrid_vector_evidence(question, evidence, settings)
                route = _route_from_tools(tools_used)
            answer_text = _compose_grounded_answer(
                question=question,
                route=route,
                evidence=evidence,
                raw_answer=response.output_text or "I could not produce an answer.",
            )
            summarized_evidence = _summarize_evidence(evidence)
            debug_payload = {"raw_evidence": evidence} if debug else None
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
                        return {
                            "answer": "There is insufficient evidence to make that legal, safety, or fraud claim from the available support-ticket evidence.",
                            "route": "vector",
                            "evidence": _summarize_evidence(evidence),
                            "debug": {"raw_evidence": evidence, "tool_errors": tool_errors} if debug else None,
                        }
                    continue
                try:
                    result = run_sql_query(settings["duckdb_path"], arguments["sql"])
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
                        return {
                            "answer": "I could not complete the request reliably with the available tool outputs. There is insufficient evidence or the generated query needs correction.",
                            "route": route,
                            "evidence": summarized_evidence,
                            "debug": debug_payload,
                        }
                    continue
            elif call.name == "run_vector_search":
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
            evidence.append({"tool": call.name, "result": result})
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": _json_dumps(_tool_result_for_model(call.name, result)),
                }
            )

        route = _route_from_tools(tools_used)
        if route == "sql" and _needs_hybrid(question):
            evidence = _supplement_hybrid_vector_evidence(question, evidence, settings)
            if any(item["tool"] == "run_vector_search" for item in evidence):
                tools_used.add("run_vector_search")

    route = _route_from_tools(tools_used)
    if route == "hybrid":
        evidence = _supplement_hybrid_vector_evidence(question, evidence, settings)
        route = _route_from_tools(tools_used)

    summarized_evidence = _summarize_evidence(evidence)
    debug_payload = {
        "raw_evidence": evidence,
        "tool_errors": tool_errors,
        "timeout_reason": "max_tool_rounds_exceeded",
    } if debug else None

    if evidence:
        return {
            "answer": _compose_grounded_answer(
                question=question,
                route=route,
                evidence=evidence,
                raw_answer="I gathered evidence, but the tool loop did not converge cleanly. Here is the grounded summary from the evidence I was able to collect.",
            ),
            "route": route,
            "evidence": summarized_evidence,
            "debug": debug_payload,
        }

    return {
        "answer": "I could not complete the request reliably because the retrieval loop did not finish cleanly. Please try again or narrow the question slightly.",
        "route": route,
        "evidence": summarized_evidence,
        "debug": debug_payload,
    }
