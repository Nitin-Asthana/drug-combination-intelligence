"""Agent 6 — Evidence Synthesis Agent (spec §5).

Reconciles evidence layers into supporting/contradictory/gaps with source-quality
and recency notes.
"""
from __future__ import annotations

import json

from agents.base import AgentContext, load_prompt
from models.schemas import EvidenceSynthesis
from services import reasoner
from services.llm import LLMUnavailable, get_llm
from agents.interaction_agent import _evidence_for_prompt


def _source_quality_notes(ctx: AgentContext) -> list:
    notes = []
    has_synthetic = any(e.provenance_status == "synthetic" for e in ctx.evidence)
    # "retrieved at runtime" should only reflect live public API pulls, not the
    # product-master identity facts (which are also marked retrieved).
    has_live = any(
        e.provenance_status == "retrieved"
        and e.evidence_layer in ("literature", "regulatory", "combination", "toxicity")
        for e in ctx.evidence
    )
    has_cached = any(e.provenance_status == "cached" for e in ctx.evidence)
    has_planned = any(e.provenance_status == "planned_not_retrieved" for e in ctx.evidence)
    if has_synthetic:
        notes.append("Internal records are synthetic demonstration data (demonstration-only weight).")
    if has_live:
        notes.append("Some evidence was retrieved from authoritative public sources at runtime.")
    if has_cached:
        notes.append("Some evidence was pre-collected from authoritative public sources (offline store).")
    if has_planned and not (has_live or has_cached):
        notes.append("Public sources were only planned (not retrieved) for this pair — no authoritative public evidence.")
    elif has_planned:
        notes.append("Some public sources are shown as a retrieval plan (not executed).")
    return notes


def run(ctx: AgentContext) -> AgentContext:
    if ctx.reasoning is None:
        ctx.reasoning = reasoner.derive_reasoning(ctx.ingredients_a, ctx.ingredients_b)
    r = ctx.reasoning

    synthesis = EvidenceSynthesis(
        supporting_evidence=list(r.supporting_evidence),
        contradictory_evidence=list(r.contradictory_evidence),
        evidence_gaps=list(r.evidence_gaps),
        source_quality_notes=_source_quality_notes(ctx),
        recency_notes=[],
        evidence_strength=r.evidence_strength,
    )

    if ctx.use_llm:
        from agents.combined_reasoning import ensure_combined_llm

        ensure_combined_llm(ctx)
        part = (ctx.combined_llm or {}).get("synthesis")
        if isinstance(part, dict):
            try:
                merged = _coerce(part)
                # always keep our deterministic source-quality provenance notes
                merged.setdefault("source_quality_notes", synthesis.source_quality_notes)
                synthesis = EvidenceSynthesis(**merged)
            except Exception:
                pass

    ctx.synthesis = synthesis
    return ctx


def _coerce(data: dict) -> dict:
    allowed = {
        "supporting_evidence",
        "contradictory_evidence",
        "evidence_gaps",
        "source_quality_notes",
        "recency_notes",
        "evidence_strength",
    }
    return {k: v for k, v in data.items() if k in allowed}
