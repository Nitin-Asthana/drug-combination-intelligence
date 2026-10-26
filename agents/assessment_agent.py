"""Agent 7 — Assessment Agent (spec §5, §9).

Produces the final structured CombinationAssessment. Enforces the controlled
vocabulary and strips any forbidden terms ("safe", "approved", ...).
"""
from __future__ import annotations

import json

from agents.base import AgentContext, load_prompt
from models.schemas import (
    FORBIDDEN_ASSESSMENT_TERMS,
    OVERALL_ASSESSMENTS,
    CombinationAssessment,
)
from services import reasoner
from services.llm import LLMUnavailable, get_llm


def _guard_overall(value: str) -> str:
    v = (value or "").strip()
    for allowed in OVERALL_ASSESSMENTS:
        if v.lower() == allowed.lower():
            return allowed
    # map partial matches
    lowered = v.lower()
    for allowed in OVERALL_ASSESSMENTS:
        if allowed.lower().startswith(lowered[:12]) and lowered:
            return allowed
    return "Insufficient Evidence"


def _contains_forbidden(text: str) -> bool:
    t = (text or "").lower()
    return any(term in t.split() for term in FORBIDDEN_ASSESSMENT_TERMS)


def run(ctx: AgentContext) -> AgentContext:
    if ctx.reasoning is None:
        ctx.reasoning = reasoner.derive_reasoning(ctx.ingredients_a, ctx.ingredients_b)
    r = ctx.reasoning

    name_a = ctx.identity_a.canonical_ingredient if ctx.identity_a and ctx.identity_a.canonical_ingredient else ctx.product_a
    name_b = ctx.identity_b.canonical_ingredient if ctx.identity_b and ctx.identity_b.canonical_ingredient else ctx.product_b

    assessment = CombinationAssessment(
        drug_a=f"{ctx.product_a} ({name_a})",
        drug_b=f"{ctx.product_b} ({name_b})",
        overall_assessment=_guard_overall(r.overall_assessment),
        benefit_signal=r.benefit_signal,
        interaction_signal=ctx.interaction.interaction_signal if ctx.interaction else r.interaction_signal,
        toxicity_signal=ctx.toxicity.toxicity_signal if ctx.toxicity else r.toxicity_signal,
        evidence_strength=ctx.synthesis.evidence_strength if ctx.synthesis else r.evidence_strength,
        confidence=int(r.confidence),
        rationale=r.mechanism_summary or "; ".join(r.why_bullets[:2]),
        why_bullets=list(r.why_bullets),
        supporting_evidence=ctx.synthesis.supporting_evidence if ctx.synthesis else list(r.supporting_evidence),
        contradictory_evidence=ctx.synthesis.contradictory_evidence if ctx.synthesis else list(r.contradictory_evidence),
        evidence_gaps=ctx.synthesis.evidence_gaps if ctx.synthesis else list(r.evidence_gaps),
        human_review_required=True,
    )

    if ctx.use_llm:
        from agents.combined_reasoning import ensure_combined_llm

        ensure_combined_llm(ctx)
        part = (ctx.combined_llm or {}).get("assessment")
        if isinstance(part, dict):
            try:
                merged = _coerce(part)
                merged["drug_a"] = assessment.drug_a
                merged["drug_b"] = assessment.drug_b
                candidate = CombinationAssessment(**merged)
                assessment = _sanitize(candidate)
            except Exception:
                pass

    ctx.assessment = _sanitize(assessment)
    return ctx


def _sanitize(assessment: CombinationAssessment) -> CombinationAssessment:
    assessment.overall_assessment = _guard_overall(assessment.overall_assessment)
    assessment.human_review_required = True
    assessment.confidence = max(0, min(100, int(assessment.confidence)))
    # Strip any bullet/rationale that asserts safety/approval.
    assessment.why_bullets = [b for b in assessment.why_bullets if not _contains_forbidden(b)]
    if _contains_forbidden(assessment.rationale):
        assessment.rationale = (
            "Rationale withheld: contained a prohibited safety/approval claim. "
            "Evidence requires researcher review."
        )
    return assessment


def _coerce(data: dict) -> dict:
    allowed = {
        "overall_assessment",
        "benefit_signal",
        "interaction_signal",
        "toxicity_signal",
        "evidence_strength",
        "confidence",
        "rationale",
        "why_bullets",
        "supporting_evidence",
        "contradictory_evidence",
        "evidence_gaps",
        "human_review_required",
    }
    return {k: v for k, v in data.items() if k in allowed}
