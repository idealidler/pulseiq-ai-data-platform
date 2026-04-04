from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from api.services.sql_service import run_sql_query
from api.services.vector_service import run_vector_search
from embeddings.config import load_settings


SYSTEM_PROMPT = """
You are PulseIQ, an analytics and support intelligence assistant.
Route each question to one or both tools:
- run_sql_query for metrics, trends, calculations, and serving-table lookups
- run_vector_search for semantic support-ticket evidence

Use only evidence returned by tools. If evidence is insufficient, say so.
Prefer SQL for numeric claims. Prefer vector search for complaint themes and customer language.
When useful, call both tools and synthesize the answer.
Default to concise answers: usually 3-5 bullets or under 180 words unless the user explicitly asks for detail.
If there is no strong evidence for a claim, explicitly say there is insufficient evidence instead of guessing.
When the answer contains multiple points, always format them as proper Markdown lists.
- Use `- ` for bullet points.
- Use `1. `, `2. ` style for numbered lists.
- Put each bullet or numbered item on its own line.
- Never cram multiple bullets into one paragraph.

For SQL queries, you must use only these existing DuckDB tables:
- mart_product_risk
- mart_revenue_daily
- mart_product_engagement_daily
- mart_support_issue_trends
- fct_support_tickets_enriched
- dim_products
- dim_customers

Do not invent table names. For example, do not use names like product_risk_scores.
Do not invent column names either. Use only the real columns below.

Table schemas:
- mart_product_risk(metric_date, product_id, product_name, category, subcategory, orders_count, units_sold, net_revenue, refund_amount, refund_rate, total_events, sessions_count, active_customers, product_views, add_to_cart_events, checkout_start_events, purchase_events, support_page_views, product_view_to_purchase_rate, complaint_count, avg_resolution_time_hours, avg_csat_score, open_tickets_count, risk_score)
- mart_revenue_daily(order_date, category, region, orders_count, units_sold, gross_revenue, discounts, net_revenue, refund_amount, refund_rate)
- mart_product_engagement_daily(event_date, product_id, category, total_events, sessions_count, active_customers, product_views, add_to_cart_events, checkout_start_events, purchase_events, support_page_views, product_view_to_purchase_rate)
- mart_support_issue_trends(created_date, product_id, category, issue_type, priority, tickets_count, avg_resolution_time_hours, avg_csat_score, open_tickets_count)
- fct_support_tickets_enriched(ticket_id, created_date, created_ts, closed_ts, customer_id, region, segment, product_id, product_name, category, subcategory, issue_type, priority, status, resolution_time_hours, csat_score, channel, ticket_text)
- dim_products(product_id, product_name, category, subcategory, base_price, launch_date, status)
- dim_customers(customer_id, signup_date, region, country, segment, acquisition_channel, is_active)

DuckDB SQL rules:
- For recent dates, use patterns like: order_date >= current_date - interval '30 days'
- Do not use DATE_SUB(...)
- Do not invent variables like threshold_value
- When grouping, every selected non-aggregated column must be included in GROUP BY
- For questions asking what customers are saying, you usually need run_vector_search, not SQL alone
""".strip()


SQL_TOOL = {
    "type": "function",
    "name": "run_sql_query",
    "description": (
        "Run read-only SQL against DuckDB. Only use these tables: "
        "mart_product_risk, mart_revenue_daily, mart_product_engagement_daily, "
        "mart_support_issue_trends, fct_support_tickets_enriched, dim_products, dim_customers."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": (
                    "A SELECT query using only these existing tables: "
                    "mart_product_risk, mart_revenue_daily, mart_product_engagement_daily, "
                    "mart_support_issue_trends, fct_support_tickets_enriched, dim_products, dim_customers."
                ),
            }
        },
        "required": ["sql"],
        "additionalProperties": False,
    },
}

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
                },
                "additionalProperties": False,
            },
        },
        "required": ["query_text"],
        "additionalProperties": False,
    },
}


def _summarize_evidence(evidence: list[dict[str, Any]], max_items: int = 3) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []

    for item in evidence:
        tool = item["tool"]
        result = item["result"]
        if tool == "run_sql_query":
            rows = result[:max_items]
            summary.append({"tool": tool, "rows": rows, "row_count": len(result)})
        elif tool == "run_vector_search":
            matches = [
                {
                    "ticket_id": match.get("ticket_id"),
                    "product_name": match.get("product_name"),
                    "issue_type": match.get("issue_type"),
                    "priority": match.get("priority"),
                    "created_date": match.get("created_date"),
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
            "rows": result[:max_items],
        }
    if tool == "run_vector_search":
        matches = [
            {
                "ticket_id": item.get("ticket_id"),
                "product_name": item.get("product_name"),
                "issue_type": item.get("issue_type"),
                "priority": item.get("priority"),
                "created_date": item.get("created_date"),
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

    semantic_terms = [
        "what are customers saying",
        "complaint themes",
        "complaining about",
        "themes show up",
        "actually saying",
        "something else",
    ]
    structured_terms = [
        "risk",
        "refund",
        "csat",
        "support page views",
        "open tickets",
        "resolution time",
    ]
    unsupported_claim_terms = ["legal", "compliance", "regulatory", "violation", "fraud"]

    if any(term in q for term in semantic_terms):
        guidance.append(
            "This question asks about customer language or complaint themes, so you must use run_vector_search."
        )
    if any(term in q for term in semantic_terms) and any(term in q for term in structured_terms):
        guidance.append(
            "This question mixes metrics with customer language, so you should use both run_sql_query and run_vector_search."
        )
    if "operational risks" in q:
        guidance.append(
            "Operational risks should be grounded in both mart_product_risk and support-ticket evidence, so use both tools."
        )
    if any(term in q for term in unsupported_claim_terms):
        guidance.append(
            "Do not infer legal/compliance/regulatory violations from generic complaints or risk scores. "
            "Use run_vector_search first, and if the retrieved evidence does not explicitly mention such violations, answer that there is insufficient evidence."
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
    if "risk" in q:
        lines.append("## Highest-risk products")
        for idx, row in enumerate(top_rows, start=1):
            risk = row.get("risk_score")
            if risk is not None:
                lines.append(f"{idx}. {row['product_name']} — risk score {risk}")
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
            lines.append("  - No direct retrieved ticket snippet was found for this product in the top evidence set.")

    lines.append("")
    lines.append("## Takeaway")
    lines.append("- Risk ranking comes from structured warehouse signals.")
    lines.append("- Complaint evidence is shown only when a retrieved support-ticket snippet matches the same product.")

    return "\n".join(lines).strip()


def answer_question(question: str, debug: bool = False) -> dict[str, Any]:
    settings = load_settings()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for chat answers.")

    client = OpenAI(api_key=api_key)
    model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
    dynamic_guidance = _question_guidance(question)
    input_items: list[dict[str, Any]] = [
        {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
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
    max_tool_errors = 3

    while True:
        response = client.responses.create(
            model=model,
            input=input_items,
            tools=[SQL_TOOL, VECTOR_TOOL],
        )

        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
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
                try:
                    result = run_sql_query(settings["duckdb_path"], arguments["sql"])
                except Exception as exc:
                    tool_errors.append({"tool": call.name, "error": str(exc)})
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(
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
                            "output": json.dumps(
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
                    "output": json.dumps(_tool_result_for_model(call.name, result)),
                }
            )
