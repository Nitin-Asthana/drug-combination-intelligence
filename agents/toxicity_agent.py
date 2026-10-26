"""Agent 5 — Toxicity Agent (spec §5).

Identifies overlapping/combination toxicity considerations, always distinguishing
a reported signal from a causal relationship.
"""
from __future__ import annotations

import json

from agents.base import AgentContext, load_prompt
from models.schemas import ToxicityAnalysis
from services import reasoner
from services.llm import LLMUnavailable, get_llm
from agents.interaction_agent import _evidence_for_prompt


def run(ctx: AgentContext) -> AgentContext:
    if ctx.reasoning is None:
        ctx.reasoning = reasoner.derive_reasoning(ctx.ingredients_a, ctx.ingredients_b)
    r = ctx.reasoning

    toxicity = ToxicityAnalysis(
        toxicity_signal=r.toxicity_signal,
        overlapping_adverse_effects=list(r.overlapping_adverse_effects),
        organ_specific_concerns=list(r.organ_concerns),
        findings=list(r.toxicity_findings),
    )

    if ctx.use_llm:
        from agents.combined_reasoning import ensure_combined_llm

        ensure_combined_llm(ctx)
        part = (ctx.combined_llm or {}).get("toxicity")
        if isinstance(part, dict):
            try:
                toxicity = ToxicityAnalysis(**_coerce(part))
            except Exception:
                pass

    ctx.toxicity = toxicity
    return ctx


def _coerce(data: dict) -> dict:
    allowed = {
        "toxicity_signal",
        "overlapping_adverse_effects",
        "organ_specific_concerns",
        "reported_signals",
        "findings",
        "evidence_item_ids",
        "causality_caveat",
    }
    return {k: v for k, v in data.items() if k in allowed}
