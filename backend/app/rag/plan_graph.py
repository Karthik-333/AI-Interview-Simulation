import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.rag.llm import LLM_AVAILABLE, generate_answer, generate_structured_json
from app.rag.vector_store import get_all_chunks

DEFAULT_RESUME_SAMPLE = 4


class PlanState(TypedDict, total=False):
    job_description: str
    resume_chunks: list[str]
    prompt: str
    plan: list[dict[str, Any]]


def _sample_resume_chunks(limit: int = DEFAULT_RESUME_SAMPLE) -> list[str]:
    return get_all_chunks(limit=limit)


def _fallback_plan(job_description: str, resume_chunks: list[str] | None = None) -> list[dict[str, Any]]:
    text = (job_description or "").strip()
    if not text:
        return []
    keywords = [
        "experience",
        "technical",
        "problem solving",
        "communication",
        "leadership",
        "domain",
    ]
    sections = []
    for index, keyword in enumerate(keywords[:4]):
        sections.append(
            {
                "label": keyword.replace(" ", " ").title(),
                "topic": keyword,
                "expectations": [
                    f"Describe {keyword} with a concrete example from your background.",
                    "Tie the example back to business or user impact.",
                ],
            }
        )
    if not sections:
        sections.append({
            "label": "Background",
            "topic": "background",
            "expectations": ["Summarize the relevant experience and motivation for this role."],
        })
    if resume_chunks:
        first = resume_chunks[0].strip()
        if first:
            sections[0]["expectations"][0] = f"Connect your experience to this resume context: {first[:160]}"
    return sections


def build_plan_prompt(job_description: str, resume_chunks: list[str] | None = None) -> str:
    context = "\n\n".join(resume_chunks or [])
    return f"""You are a hiring manager designing an interview plan for the position below.

    Produce strict JSON with this shape:
    {{
      "sections": [
        {{
          "label": "<short section title>",
          "topic": "<focus area>",
          "expectations": ["<explicit evidence expected>", "<optional second expectation>"]
        }}
      ]
    }}

    The plan should be ordered, practical, and tailored to the job description and resume context. Each section should list 2-3 explicit expectations about what a strong answer should demonstrate.

    Job description:
    {job_description}

    Resume context:
    {context or 'No resume context available.'}

    JSON:
    """


def compose_plan_prompt(state: PlanState) -> PlanState:
    return {**state, "prompt": build_plan_prompt(state.get("job_description", ""), state.get("resume_chunks", []))}


def generate_plan(state: PlanState) -> PlanState:
    raw = generate_structured_json(state["prompt"])
    plan = (raw or {}).get("sections") if isinstance(raw, dict) else None
    if not plan:
        plan = _fallback_plan(state.get("job_description", ""), state.get("resume_chunks", []))
    return {**state, "plan": plan}


def build_plan_graph():
    graph = StateGraph(PlanState)
    graph.add_node("compose_plan_prompt", compose_plan_prompt)
    graph.add_node("generate_plan", generate_plan)
    graph.set_entry_point("compose_plan_prompt")
    graph.add_edge("compose_plan_prompt", "generate_plan")
    graph.add_edge("generate_plan", END)
    return graph.compile()


plan_graph = build_plan_graph()


def run_plan_generation(job_description: str | None = None, resume_context: list[str] | None = None) -> list[dict[str, Any]] | None:
    """Generate a structured interview plan for a JD-backed session."""
    if not job_description or not job_description.strip():
        return None
    if not LLM_AVAILABLE:
        return _fallback_plan(job_description, resume_context or _sample_resume_chunks())

    resume_chunks = resume_context or _sample_resume_chunks()
    result = plan_graph.invoke({"job_description": job_description, "resume_chunks": resume_chunks})
    plan = result.get("plan") or _fallback_plan(job_description, resume_chunks)
    normalized = []
    for index, section in enumerate(plan):
        if not isinstance(section, dict):
            continue
        label = str(section.get("label") or section.get("topic") or f"Section {index + 1}")
        topic = str(section.get("topic") or label)
        expectations = section.get("expectations") or []
        normalized.append({
            "label": label,
            "topic": topic,
            "expectations": [str(item) for item in expectations if str(item).strip()],
        })
    return normalized or _fallback_plan(job_description, resume_chunks)
