from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.services.chat_service import answer_question


ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_PATH = ROOT / "evals" / "test_cases.json"
RESULTS_DIR = ROOT / "evals" / "results"


def load_test_cases() -> list[dict[str, Any]]:
    return json.loads(TEST_CASES_PATH.read_text())


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(v) for v in value.values())
    return str(value).lower()


def _tool_names(raw_evidence: list[dict[str, Any]]) -> list[str]:
    return [item.get("tool", "") for item in raw_evidence]


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    try:
        result = answer_question(case["question"], debug=True)
    except Exception as exc:
        return {
            "id": case["id"],
            "question": case["question"],
            "expected_route": case["expected_route"],
            "actual_route": "error",
            "tools_used": [],
            "answer_word_count": 0,
            "checks": {
                "route_ok": False,
                "tools_ok": False,
                "keyword_ok": False,
                "concise_ok": False,
                "evidence_present": False,
            },
            "score": 0.0,
            "answer": "",
            "evidence": [],
            "error": str(exc),
        }

    raw_evidence = (result.get("debug") or {}).get("raw_evidence", [])
    tools_used = _tool_names(raw_evidence)
    answer_text = result.get("answer", "")
    answer_word_count = len(answer_text.split())
    flattened_answer = answer_text.lower()
    flattened_evidence = _flatten_text(raw_evidence)

    route_ok = result.get("route") == case["expected_route"]
    tools_ok = all(tool in tools_used for tool in case.get("required_evidence_tools", []))
    keywords = case.get("answer_keywords_any", [])
    keyword_ok = any(keyword in flattened_answer or keyword in flattened_evidence for keyword in keywords)
    concise_ok = answer_word_count <= case.get("max_answer_words", 180)
    evidence_present = len(raw_evidence) > 0

    checks = {
        "route_ok": route_ok,
        "tools_ok": tools_ok,
        "keyword_ok": keyword_ok,
        "concise_ok": concise_ok,
        "evidence_present": evidence_present,
    }
    score = sum(1 for passed in checks.values() if passed) / len(checks)

    return {
        "id": case["id"],
        "question": case["question"],
        "expected_route": case["expected_route"],
        "actual_route": result.get("route"),
        "tools_used": tools_used,
        "answer_word_count": answer_word_count,
        "checks": checks,
        "score": round(score, 2),
        "answer": answer_text,
        "evidence": result.get("evidence", []),
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    avg_score = round(sum(item["score"] for item in results) / total, 2) if total else 0.0
    passed = sum(1 for item in results if item["score"] == 1.0)
    error_count = sum(1 for item in results if item.get("actual_route") == "error")

    route_accuracy = round(
        sum(1 for item in results if item["checks"]["route_ok"]) / total, 2
    ) if total else 0.0
    conciseness_rate = round(
        sum(1 for item in results if item["checks"]["concise_ok"]) / total, 2
    ) if total else 0.0

    return {
        "total_cases": total,
        "perfect_cases": passed,
        "error_cases": error_count,
        "average_score": avg_score,
        "route_accuracy": route_accuracy,
        "conciseness_rate": conciseness_rate,
    }


def main() -> None:
    cases = load_test_cases()
    results = [evaluate_case(case) for case in cases]
    summary = summarize_results(results)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"eval_results_{timestamp}.json"
    output_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2))

    print("Evaluation summary:")
    print(json.dumps(summary, indent=2))
    print(f"Saved detailed results to {output_path}")


if __name__ == "__main__":
    main()
