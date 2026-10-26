"""One-shot combined LLM reasoning.

When Azure is enabled, the interaction / toxicity / synthesis / assessment agents
share a SINGLE gpt call instead of four sequential ones. The result is memoized
on the context so each agent simply reads its slice.
"""
from __future__ import annotations

import json
from typing import List

from agents.base import AgentContext, load_prompt
from services import reasoner
from services.llm import LLMUnavailable, get_llm


def _evidence_for_prompt(ctx: AgentContext) -> List[dict]:
    items = []
    for i, e in enumerate(ctx.evidence):
        summary = e.evidence_excerpt_or_summary or ""
        if len(summary) > 220:
            summary = summary[:220] + "…"
        items.append(
            {
                "index": i,
                "source_name": e.source_name,
                "authority_level": e.authority_level,
                "provenance_status": e.provenance_status,
                "evidence_layer": e.evidence_layer,
                "summary": summary,
            }
        )
    return items[:14]  # cap payload size for latency


def ensure_combined_llm(ctx: AgentContext) -> None:
    """Run the combined reasoning call once; store result on ctx.combined_llm."""
    if ctx.combined_llm_attempted:
        return
    ctx.combined_llm_attempted = True

    if not ctx.use_llm:
        return

    # Ensure the deterministic drug-class reasoning exists; pass it to the model
    # as a labelled prior so it can produce a grounded, differentiated assessment
    # rather than defaulting everything to "Insufficient Evidence".
    if ctx.reasoning is None:
        ctx.reasoning = reasoner.derive_reasoning(ctx.ingredients_a, ctx.ingredients_b)
    r = ctx.reasoning

    try:
        llm = get_llm()
        payload = {
            "drug_a": ctx.identity_a.canonical_ingredient if ctx.identity_a and ctx.identity_a.canonical_ingredient else ctx.product_a,
            "drug_b": ctx.identity_b.canonical_ingredient if ctx.identity_b and ctx.identity_b.canonical_ingredient else ctx.product_b,
            "product_a": ctx.product_a,
            "product_b": ctx.product_b,
            "research_question": ctx.research_question,
            "identity_a": ctx.identity_a.model_dump() if ctx.identity_a else {},
            "identity_b": ctx.identity_b.model_dump() if ctx.identity_b else {},
            "demonstration_heuristic": {
                "overall_assessment": r.overall_assessment,
                "benefit_signal": r.benefit_signal,
                "interaction_signal": r.interaction_signal,
                "toxicity_signal": r.toxicity_signal,
                "interaction_class": r.interaction_class,
                "mechanism_summary": r.mechanism_summary,
                "why": r.why_bullets,
                "overlapping_adverse_effects": r.overlapping_adverse_effects,
                "organ_concerns": r.organ_concerns,
                "note": "Prior derived from general drug-class pharmacology (demonstration-level). "
                        "Use it as a starting hypothesis; corroborate or temper it with the retrieved "
                        "evidence. When retrieved evidence is consistent or silent, you may adopt these "
                        "signal levels, clearly reflecting demonstration-level confidence.",
            },
            "evidence": _evidence_for_prompt(ctx),
        }
        data = llm.complete_json(
            load_prompt("combined"),
            json.dumps(payload, ensure_ascii=False),
        )
        if isinstance(data, dict):
            ctx.combined_llm = data
    except (LLMUnavailable, Exception):
        ctx.combined_llm = None
