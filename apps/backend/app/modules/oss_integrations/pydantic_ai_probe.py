from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel, Field


class CandidateSignal(BaseModel):
    label: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class PydanticAIProbeOutput(BaseModel):
    summary: str = Field(min_length=1)
    signals: list[CandidateSignal] = Field(min_length=1)
    approval_required: bool


class PydanticAIProbeResult(BaseModel):
    status: str
    engine: str
    model: str
    output: PydanticAIProbeOutput


def run_pydantic_ai_probe() -> PydanticAIProbeResult:
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.test import TestModel
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="PydanticAI is not installed in this backend environment. Rebuild the backend image.",
        ) from exc

    agent = Agent(
        TestModel(),
        output_type=PydanticAIProbeOutput,
        instructions=(
            "Return a structured JobCopilot resume signal check. "
            "The output must include a summary, at least one signal, and whether approval is required."
        ),
    )
    result = agent.run_sync("Probe PydanticAI structured output for JobCopilot.")
    output = result.output

    return PydanticAIProbeResult(
        status="complete",
        engine="pydantic-ai",
        model="test",
        output=output,
    )
