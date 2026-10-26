"""Agent 4 — Interaction Agent (spec §5).

Determines the interaction class/signal. Deterministic reasoning is computed
first (and stored on the context for downstream agents). When Azure is enabled,
the LLM refines the analysis using the gathered evidence; its output is validated
into the Pydantic schema and falls back to the deterministic result on failure.
"""
from __future__ import annotations

import json

from agents.base import AgentContext, load_prompt
from models.schemas import InteractionAnalysis
from services import reasoner
from services.llm import LLMUnavailable, get_llm


def _evidence_for_prompt(ctx: AgentContext) -> list:
    return [
        {
            "index": i,
            "source_name": e.source_name,
            "authority_level": e.authority_level,
            "provenance_status": e.provenance_status,
            "summary": e.evidence_excerpt_or_summary,
        }
        for i, e in enumerate(ctx.evidence)
    ]


def run(ctx: AgentContext) -> AgentContext:
    # deterministic reasoning core (also used by toxicity/synthesis/assessment)
    if ctx.reasoning is None:
        ctx.reasoning = reasoner.derive_reasoning(ctx.ingredients_a, ctx.ingredients_b)
    r = ctx.reasoning

    interaction = InteractionAnalysis(
        interaction_class=r.interaction_class,
        interaction_signal=r.interaction_signal,
        mechanism_summary=r.mechanism_summary,
        findings=list(r.interaction_findings),
    )

    if ctx.use_llm:
        from agents.combined_reasoning import ensure_combined_llm

        ensure_combined_llm(ctx)
        part = (ctx.combined_llm or {}).get("interaction")
        if isinstance(part, dict):
            try:
                interaction = InteractionAnalysis(**_coerce_interaction(part))
            except Exception:
                pass  # keep deterministic result

    ctx.interaction = interaction
    return ctx


def _coerce_interaction(data: dict) -> dict:
    allowed = {
        "interaction_class",
        "interaction_signal",
        "mechanism_summary",
        "findings",
        "evidence_item_ids",
        "caveat",
    }
    return {k: v for k, v in data.items() if k in allowed}
