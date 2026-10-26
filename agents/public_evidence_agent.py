"""Agent 3 — Public Evidence Agent (spec §5).

Uses controlled public sources only. In demo mode it constructs a transparent
retrieval plan from the authorised source registry + collection recipes. When
live retrieval is enabled it queries public APIs (PubMed, openFDA, ...).
"""
from __future__ import annotations

from agents.base import AgentContext
from services import collected_store
from services import retrieval


def run(ctx: AgentContext) -> AgentContext:
    ing_a = ctx.primary_ingredient_a()
    ing_b = ctx.primary_ingredient_b()

    if ctx.live_retrieval:
        live = retrieval.live_public_retrieval(ing_a, ing_b)
        ctx.evidence.extend(live)
        # Still show the plan for sources not covered by live adapters.
        if not live:
            ctx.evidence.extend(retrieval.build_public_plan(ing_a, ing_b))
    else:
        # Fully-offline path: prefer real pre-collected evidence if available,
        # otherwise fall back to a transparent retrieval plan.
        cached = collected_store.load_evidence(ing_a, ing_b)
        if cached:
            ctx.evidence.extend(cached)
        else:
            ctx.evidence.extend(retrieval.build_public_plan(ing_a, ing_b))
    return ctx
