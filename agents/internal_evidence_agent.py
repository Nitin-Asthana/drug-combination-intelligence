"""Agent 2 — Internal Evidence Agent (spec §5).

Searches the synthetic internal combination research dataset. Results are always
labelled synthetic demonstration data.
"""
from __future__ import annotations

from agents.base import AgentContext
from services import retrieval


def run(ctx: AgentContext) -> AgentContext:
    items = retrieval.search_internal(ctx.ingredients_a, ctx.ingredients_b)
    ctx.evidence.extend(items)
    return ctx
