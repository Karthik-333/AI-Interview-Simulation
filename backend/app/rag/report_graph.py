"""Report generation graph for analyzing interview transcripts against a plan."""

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.rag.llm import LLM_AVAILABLE, generate_answer
from app.services.scoring_service import semantic_match, validate_factuality


class ReportState(TypedDict, total=False):
    plan: list[dict[str, Any]]
    history: list[dict[str, Any]]
    prompt: str
    report: list[dict[str, Any]]


EXPECTATION_SCORE_MAPPING = {
    "met": 3,
    "partially": 2,
    "not met": 1,
    "not assessed": 0,
}

EXPECTATION_LABELS = {
    3: "Met",
    2: "Partially Met",
    1: "Not Met",
    0: "Not Assessed",
}


def _find_supporting_turn(expectation: str, history: list[dict]) -> tuple[dict | None, int]:
    """Find the turn that best supports an expectation, or None."""
    best_match = (None, 0.0, -1)
    for idx, entry in enumerate(history):
        answer = entry.get("answer", "")
        match_score = semantic_match(answer, expectation)
        if match_score > best_match[1]:
            best_match = (entry, match_score, idx)
    if best_match[1] > 0.2:
        return best_match[0], best_match[2]
    return None, -1


def _assess_expectation(
    expectation: str,
    history: list[dict],
    threshold_met: float = 0.5,
    threshold_partial: float = 0.2,
) -> tuple[int, int, str]:
    """Assess if an expectation is met, partially met, not met, or not assessed.
    Returns (score, turn_index, evidence).
    """
    supporting_turn, turn_idx = _find_supporting_turn(expectation, history)
    if supporting_turn is None:
        return 0, -1, "No relevant evidence found in transcript."
    answer = supporting_turn.get("answer", "")
    match_score = semantic_match(answer, expectation)
    if match_score >= threshold_met:
        return 3, turn_idx, f"Strong evidence in turn {turn_idx + 1}."
    elif match_score >= threshold_partial:
        return 2, turn_idx, f"Partial evidence in turn {turn_idx + 1}."
    else:
        return 1, turn_idx, f"Weak evidence in turn {turn_idx + 1}."


def _compose_report_prompt(plan: list[dict], history: list[dict]) -> str:
    """Compose a prompt for structured report generation."""
    sections_text = ""
    for i, section in enumerate(plan):
        label = section.get("label") or section.get("topic") or f"Section {i + 1}"
        expectations = section.get("expectations") or []
        exp_text = "; ".join(expectations) if expectations else "No specific expectations."
        sections_text += f"\n{i + 1}. {label}: {exp_text}"

    transcript_text = ""
    for i, entry in enumerate(history):
        q = entry.get("question", "")
        a = entry.get("answer", "")
        s = entry.get("score", 0)
        transcript_text += f"\nTurn {i + 1} (Score: {s}/10):\n  Q: {q}\n  A: {a[:200]}...\n"

    return f"""Generate a structured interview assessment report.

Interview Plan Sections (with expectations):
{sections_text}

Interview Transcript:
{transcript_text}

For each expectation, rate it as:
- "Met" (3): Strong evidence of the expectation being demonstrated
- "Partially Met" (2): Some evidence but incomplete
- "Not Met" (1): Evidence exists but doesn't satisfy the expectation
- "Not Assessed" (0): No relevant evidence in the transcript

Output as strict JSON:
{{
  "report": [
    {{
      "section_label": "<label>",
      "section_index": <int>,
      "expectations": [
        {{
          "text": "<expectation>",
          "score": <0-3>,
          "label": "<Met|Partially Met|Not Met|Not Assessed>",
          "evidence": "<brief description of supporting turn or absence>"
        }}
      ]
    }}
  ],
  "overall_assessment": "<2-3 sentence summary of interview performance>"
}}

JSON:
"""


def compose_report_prompt(state: ReportState) -> ReportState:
    prompt = _compose_report_prompt(state.get("plan", []), state.get("history", []))
    return {**state, "prompt": prompt}


def generate_report_from_prompt(state: ReportState) -> ReportState:
    if not LLM_AVAILABLE:
        return _generate_report_heuristic(state)
    raw = generate_answer(state["prompt"])
    try:
        import re

        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            report = data.get("report", [])
            return {**state, "report": report}
    except Exception:
        pass
    return _generate_report_heuristic(state)


def _generate_report_heuristic(state: ReportState) -> ReportState:
    """Fallback report generation using deterministic heuristics."""
    plan = state.get("plan", [])
    history = state.get("history", [])
    report = []

    for idx, section in enumerate(plan):
        label = section.get("label") or section.get("topic") or f"Section {idx + 1}"
        expectations = section.get("expectations") or []
        exp_reports = []

        for expectation in expectations:
            score, turn_idx, evidence = _assess_expectation(expectation, history)
            exp_reports.append({
                "text": expectation,
                "score": score,
                "label": EXPECTATION_LABELS.get(score, "Not Assessed"),
                "evidence": evidence,
            })

        report.append({
            "section_label": label,
            "section_index": idx,
            "expectations": exp_reports,
        })

    return {**state, "report": report}


def build_report_graph():
    graph = StateGraph(ReportState)
    graph.add_node("compose_report_prompt", compose_report_prompt)
    graph.add_node("generate_report", generate_report_from_prompt)
    graph.set_entry_point("compose_report_prompt")
    graph.add_edge("compose_report_prompt", "generate_report")
    graph.add_edge("generate_report", END)
    return graph.compile()


report_graph = build_report_graph()


def run_report_generation(plan: list[dict], history: list[dict]) -> dict[str, Any] | None:
    """Generate a comprehensive interview report against a plan.
    Returns dict with report sections and overall assessment, or None if inputs are invalid.
    """
    if not plan or not history:
        return None
    result = report_graph.invoke({"plan": plan, "history": history})
    report = result.get("report") or []
    return {
        "plan": plan,
        "history_count": len(history),
        "report": report,
    }
