from __future__ import annotations

from typing import TypedDict

from fastapi import HTTPException
from pydantic import BaseModel


class LangGraphProbeState(TypedDict):
    run_id: str
    steps: list[str]
    current_step: str
    status: str


class LangGraphProbeResult(BaseModel):
    status: str
    engine: str
    run_id: str
    current_step: str
    steps: list[str]


def _auth(state: LangGraphProbeState) -> LangGraphProbeState:
    return {
        **state,
        "current_step": "auth",
        "steps": [*state["steps"], "auth:complete"],
    }


def _resume_intake(state: LangGraphProbeState) -> LangGraphProbeState:
    return {
        **state,
        "current_step": "resume_intake",
        "steps": [*state["steps"], "resume_intake:complete"],
    }


def _review_queue(state: LangGraphProbeState) -> LangGraphProbeState:
    return {
        **state,
        "current_step": "review_queue",
        "status": "complete",
        "steps": [*state["steps"], "review_queue:complete"],
    }


def run_langgraph_probe() -> LangGraphProbeResult:
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="LangGraph is not installed in this backend environment. Rebuild the backend image.",
        ) from exc

    workflow = StateGraph(LangGraphProbeState)
    workflow.add_node("auth", _auth)
    workflow.add_node("resume_intake", _resume_intake)
    workflow.add_node("review_queue", _review_queue)
    workflow.add_edge(START, "auth")
    workflow.add_edge("auth", "resume_intake")
    workflow.add_edge("resume_intake", "review_queue")
    workflow.add_edge("review_queue", END)

    graph = workflow.compile()
    result = graph.invoke(
        {
            "run_id": "langgraph_probe",
            "steps": [],
            "current_step": "not_started",
            "status": "running",
        }
    )

    return LangGraphProbeResult(
        status=result["status"],
        engine="langgraph",
        run_id=result["run_id"],
        current_step=result["current_step"],
        steps=result["steps"],
    )
