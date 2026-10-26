"""Pydantic structured-output contracts for the agent pipeline.

Every agent returns a typed object. Free-form model text is never accepted
where a structured object is expected (see build spec §9).
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------
OVERALL_ASSESSMENTS = [
    "Potentially Beneficial",
    "Potential Concern",
    "Potentially Toxic",
    "Neutral / No meaningful interaction identified",
    "Insufficient Evidence",
]

# Terms the assessment must never emit (spec §7 / §14).
FORBIDDEN_ASSESSMENT_TERMS = ["approved", "allowed", "safe", "effective", "recommended"]

SIGNAL_LEVELS = ["None", "Low", "Moderate", "High", "Unknown"]
EVIDENCE_STRENGTHS = ["None", "Low", "Moderate", "High"]

INTERACTION_CLASSES = [
    "Known interaction",
    "Possible interaction",
    "Pharmacokinetic interaction",
    "Pharmacodynamic interaction",
    "Additive effect",
    "Antagonism",
    "No interaction identified",
    "Insufficient evidence",
]

AUTHORITY_LEVELS = [
    "Official regulatory labeling",
    "Peer-reviewed primary study",
    "Curated scientific database",
    "Manufacturer public site",
    "Internal synthetic demo data",
    "Demonstration heuristic",
    "Secondary website",
]


# ---------------------------------------------------------------------------
# Drug identity
# ---------------------------------------------------------------------------
class DrugIdentity(BaseModel):
    """Canonical identity for one product/drug (spec Agent 1)."""

    product_name: str
    canonical_ingredient: str = ""
    aliases: List[str] = Field(default_factory=list)
    identifiers: dict = Field(default_factory=dict)  # e.g. {"rxnorm": ..., "pubchem_cid": ...}
    dosage_form: str = ""
    therapeutic_category: str = ""
    composition: str = ""
    identity_confidence: str = "Unknown"  # High / Moderate / Low / Unknown
    source_references: List[str] = Field(default_factory=list)
    resolved: bool = False
    note: str = ""


# ---------------------------------------------------------------------------
# Evidence item with full provenance (spec §11)
# ---------------------------------------------------------------------------
class EvidenceItem(BaseModel):
    source_name: str
    source_type: str  # internal_synthetic / regulatory_label / literature / combination_dataset / product_master / demonstration
    source_url: str = ""
    source_identifier: str = ""  # PMID, CID, label ID, etc.
    retrieved_date: str = ""
    evidence_excerpt_or_summary: str = ""
    authority_level: str = "Demonstration heuristic"
    provenance_status: str = "demonstration"  # retrieved / cached / planned_not_retrieved / synthetic / demonstration
    evidence_layer: str = "public"  # internal / regulatory / literature / combination / toxicity / identity

    @property
    def is_synthetic(self) -> bool:
        return self.provenance_status in ("synthetic",) or "synthetic" in self.source_type


# ---------------------------------------------------------------------------
# Interaction analysis (Agent 4)
# ---------------------------------------------------------------------------
class InteractionAnalysis(BaseModel):
    interaction_class: str = "Insufficient evidence"
    interaction_signal: str = "Unknown"  # SIGNAL_LEVELS
    mechanism_summary: str = ""
    findings: List[str] = Field(default_factory=list)
    evidence_item_ids: List[int] = Field(default_factory=list)
    caveat: str = "Absence of evidence is not evidence of safety."


# ---------------------------------------------------------------------------
# Toxicity analysis (Agent 5)
# ---------------------------------------------------------------------------
class ToxicityAnalysis(BaseModel):
    toxicity_signal: str = "Unknown"  # SIGNAL_LEVELS
    overlapping_adverse_effects: List[str] = Field(default_factory=list)
    organ_specific_concerns: List[str] = Field(default_factory=list)
    reported_signals: List[str] = Field(default_factory=list)  # explicitly "reported", not causal
    findings: List[str] = Field(default_factory=list)
    evidence_item_ids: List[int] = Field(default_factory=list)
    causality_caveat: str = (
        "Reported adverse-event signals are not proof of causality."
    )


# ---------------------------------------------------------------------------
# Evidence synthesis (Agent 6)
# ---------------------------------------------------------------------------
class EvidenceSynthesis(BaseModel):
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    source_quality_notes: List[str] = Field(default_factory=list)
    recency_notes: List[str] = Field(default_factory=list)
    evidence_strength: str = "Low"  # EVIDENCE_STRENGTHS


# ---------------------------------------------------------------------------
# Final combination assessment (Agent 7 / spec §9)
# ---------------------------------------------------------------------------
class CombinationAssessment(BaseModel):
    drug_a: str
    drug_b: str
    overall_assessment: str = "Insufficient Evidence"
    benefit_signal: str = "Unknown"
    interaction_signal: str = "Unknown"
    toxicity_signal: str = "Unknown"
    evidence_strength: str = "Low"
    confidence: int = 0  # AI synthesis confidence 0-100, NOT probability of efficacy
    rationale: str = ""
    why_bullets: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    human_review_required: bool = True


# ---------------------------------------------------------------------------
# Full pipeline result carried through the UI
# ---------------------------------------------------------------------------
class AnalysisResult(BaseModel):
    identity_a: DrugIdentity
    identity_b: DrugIdentity
    evidence: List[EvidenceItem] = Field(default_factory=list)
    interaction: InteractionAnalysis
    toxicity: ToxicityAnalysis
    synthesis: EvidenceSynthesis
    assessment: CombinationAssessment
    mode: str = "demo"  # "demo" or "azure"
    live_retrieval_used: bool = False
    research_question: str = ""

    def evidence_counts(self) -> dict:
        counts = {
            "internal": 0,
            "regulatory": 0,
            "literature": 0,
            "combination": 0,
        }
        for item in self.evidence:
            # Only count real evidence, not un-executed query plans.
            if item.provenance_status == "planned_not_retrieved":
                continue
            layer = item.evidence_layer
            if layer in ("internal",):
                counts["internal"] += 1
            elif layer in ("regulatory", "toxicity"):
                counts["regulatory"] += 1
            elif layer in ("literature",):
                counts["literature"] += 1
            elif layer in ("combination",):
                counts["combination"] += 1
        return counts

    def planned_query_count(self) -> int:
        return sum(1 for e in self.evidence if e.provenance_status == "planned_not_retrieved")
