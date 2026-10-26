"""Deterministic reasoning core.

Produces a :class:`PairReasoning` for a drug pair by combining, in priority
order:
  1. curated demonstration reasoning (services.demo_knowledge)
  2. matched synthetic internal records (clearly demonstration-only)
  3. a conservative default of "Insufficient Evidence"

Absence of evidence is never converted to a "safe" verdict.
"""
from __future__ import annotations

from typing import List, Optional

from services import data_access as da
from services import demo_knowledge as dk
from services.demo_knowledge import PairReasoning

_SEVERITY = {
    "Potentially Toxic": 5,
    "Potential Concern": 4,
    "Potentially Beneficial": 3,
    "Neutral": 2,
    "Insufficient Evidence": 1,
}


def _match_internal(ingredients_a: List[str], ingredients_b: List[str]) -> List[dict]:
    df = da.internal_research()
    tokens_a = {i.strip().lower() for i in ingredients_a if i.strip()}
    tokens_b = {i.strip().lower() for i in ingredients_b if i.strip()}
    out = []
    for _, row in df.iterrows():
        a = str(row.get("drug_a", "")).strip().lower()
        b = str(row.get("drug_b", "")).strip().lower()
        # Require BOTH record drugs to map to the two selected drugs, so a single
        # shared ingredient paired with a placeholder compound does not count.
        if (a in tokens_a and b in tokens_b) or (a in tokens_b and b in tokens_a):
            out.append(row.to_dict())
    return out


def _reasoning_from_internal(records: List[dict]) -> PairReasoning:
    # pick the most severe synthetic record to shape the demonstration verdict
    records_sorted = sorted(
        records,
        key=lambda r: _SEVERITY.get(str(r.get("effect_category", "")).strip(), 0),
        reverse=True,
    )
    top = records_sorted[0]
    effect = str(top.get("effect_category", "")).strip() or "Insufficient Evidence"
    tox = str(top.get("toxicity_signal", "")).strip() or "Unknown"
    assessment_map = {
        "Potentially Beneficial": "Potentially Beneficial",
        "Neutral": "Neutral / No meaningful interaction identified",
        "Potential Concern": "Potential Concern",
        "Potentially Toxic": "Potentially Toxic",
        "Insufficient Evidence": "Insufficient Evidence",
    }
    overall = assessment_map.get(effect, "Insufficient Evidence")
    benefit = "Moderate" if effect == "Potentially Beneficial" else "Low"
    interaction_signal = "Moderate" if effect in ("Potential Concern", "Potentially Toxic") else "Low"
    return PairReasoning(
        overall_assessment=overall,
        benefit_signal=benefit,
        interaction_signal=interaction_signal,
        toxicity_signal=tox if tox in ("None", "Low", "Moderate", "High", "Unknown") else "Unknown",
        evidence_strength="Low",  # synthetic-only => low real-world strength
        interaction_class="Insufficient evidence"
        if effect == "Insufficient Evidence"
        else "Possible interaction",
        confidence=40,
        why_bullets=[
            f"Synthetic internal record {top.get('internal_evidence_id', '')} indicates: "
            f"{top.get('observed_effect', '')}.",
            "This is SYNTHETIC demonstration data, not real research or clinical evidence.",
            "No authoritative public finding was retrieved for this specific pair in demo mode.",
        ],
        interaction_findings=[str(top.get("observed_effect", ""))],
        toxicity_findings=[
            f"Synthetic toxicity signal: {tox}." if tox else "No synthetic toxicity signal recorded.",
        ],
        supporting_evidence=[
            f"Synthetic internal record ({top.get('internal_evidence_id', '')}) — demonstration only.",
        ],
        evidence_gaps=[
            "Authoritative public evidence (label, literature, combination datasets) not retrieved in demo mode.",
        ],
        mechanism_summary=str(top.get("mechanism_hypothesis", "")),
    )


def _default_insufficient() -> PairReasoning:
    return PairReasoning(
        overall_assessment="Insufficient Evidence",
        benefit_signal="Unknown",
        interaction_signal="Unknown",
        toxicity_signal="Unknown",
        evidence_strength="Low",
        interaction_class="Insufficient evidence",
        confidence=30,
        why_bullets=[
            "No curated demonstration reasoning and no matching internal records for this pair.",
            "Absence of retrieved evidence is NOT evidence of safety.",
            "Enable live retrieval or Azure synthesis, and require researcher review.",
        ],
        interaction_findings=["No interaction evidence retrieved."],
        toxicity_findings=["No toxicity evidence retrieved."],
        evidence_gaps=[
            "No internal, regulatory, literature or combination evidence retrieved in demo mode.",
        ],
        mechanism_summary="",
    )


def derive_reasoning(ingredients_a: List[str], ingredients_b: List[str]) -> PairReasoning:
    curated = dk.reason_about_pair(ingredients_a, ingredients_b)
    if curated is not None:
        return curated
    internal = _match_internal(ingredients_a, ingredients_b)
    if internal:
        return _reasoning_from_internal(internal)
    return _default_insufficient()
