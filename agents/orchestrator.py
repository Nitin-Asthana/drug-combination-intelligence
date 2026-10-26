"""Agent orchestration layer (spec §4).

Runs the visible workflow:
  NORMALIZE → INTERNAL → PUBLIC COMBINATION/SAFETY/LITERATURE →
  INTERACTION → TOXICITY → SYNTHESIS → ASSESSMENT → HUMAN REVIEW

``run_pipeline`` is a generator that yields (step_label, status) tuples so the
Streamlit UI can render live progress, then finally yields the AnalysisResult.
"""
from __future__ import annotations

from typing import Iterator, Tuple, Union

from agents import (
    assessment_agent,
    evidence_synthesis_agent,
    identity_agent,
    interaction_agent,
    internal_evidence_agent,
    public_evidence_agent,
    toxicity_agent,
)
from agents.base import AgentContext
from models.schemas import AnalysisResult

# Ordered workflow steps shown to the user.
WORKFLOW_STEPS = [
    ("Normalize drugs", "identity"),
    ("Search internal knowledge", "internal"),
    ("Search public combination & safety evidence", "public"),
    ("Analyze interactions", "interaction"),
    ("Analyze toxicity", "toxicity"),
    ("Synthesize evidence", "synthesis"),
    ("Produce combination assessment", "assessment"),
]

_STEP_FUNCS = {
    "identity": identity_agent.run,
    "internal": internal_evidence_agent.run,
    "public": public_evidence_agent.run,
    "interaction": interaction_agent.run,
    "toxicity": toxicity_agent.run,
    "synthesis": evidence_synthesis_agent.run,
    "assessment": assessment_agent.run,
}


def run_pipeline(
    product_a: str,
    product_b: str,
    research_question: str = "",
    use_llm: bool = False,
    live_retrieval: bool = False,
) -> Iterator[Union[Tuple[str, str], AnalysisResult]]:
    ctx = AgentContext(
        product_a=product_a,
        product_b=product_b,
        research_question=research_question,
        use_llm=use_llm,
        live_retrieval=live_retrieval,
    )

    for label, key in WORKFLOW_STEPS:
        yield (label, "running")
        _STEP_FUNCS[key](ctx)
        yield (label, "done")

    result = AnalysisResult(
        identity_a=ctx.identity_a,
        identity_b=ctx.identity_b,
        evidence=ctx.evidence,
        interaction=ctx.interaction,
        toxicity=ctx.toxicity,
        synthesis=ctx.synthesis,
        assessment=ctx.assessment,
        mode="azure" if use_llm else "demo",
        live_retrieval_used=live_retrieval,
        research_question=research_question,
    )
    yield result


def analyze(
    product_a: str,
    product_b: str,
    research_question: str = "",
    use_llm: bool = False,
    live_retrieval: bool = False,
) -> AnalysisResult:
    """Non-streaming convenience wrapper (used by tests)."""
    result: AnalysisResult | None = None
    for item in run_pipeline(
        product_a, product_b, research_question, use_llm, live_retrieval
    ):
        if isinstance(item, AnalysisResult):
            result = item
    assert result is not None
    return result
