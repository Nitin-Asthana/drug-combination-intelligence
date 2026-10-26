"""Deterministic demonstration knowledge engine (offline demo mode).

This module powers the app when Azure OpenAI is unavailable. It produces
*deterministic* assessments so the leadership demo is reproducible.

Honesty rules honoured here (spec §6, §14, §15):
  * No fabricated citations, PMIDs, or numeric synergy scores.
  * Every derived statement is labelled a "Demonstration heuristic" drawing on
    general drug-class pharmacology, not on retrieved primary evidence.
  * Absence of evidence is never converted to "safe".
  * Synthetic internal records remain labelled synthetic.

The heuristics below reference broadly established, textbook-level drug-class
considerations (e.g. NSAID + corticosteroid GI risk). They are intentionally
qualitative and are surfaced as demonstration reasoning requiring human review,
not as validated pharmacological findings for a specific product pair.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Ingredient -> drug class (normalized ingredient names, lower case)
# ---------------------------------------------------------------------------
INGREDIENT_CLASS: Dict[str, str] = {
    "levonadifloxacin": "fluoroquinolone antibacterial",
    "levetiracetam": "antiepileptic",
    "gabapentin": "gabapentinoid",
    "pregabalin": "gabapentinoid",
    "nortriptyline": "tricyclic antidepressant",
    "methylcobalamin": "vitamin b12",
    "mecobalamin": "vitamin b12",
    "hydroxocobalamin": "vitamin b12",
    "alpha lipoic acid": "antioxidant supplement",
    "pyridoxine": "vitamin b6",
    "folic acid": "vitamin",
    "cholecalciferol": "vitamin d",
    "etoricoxib": "cox-2 selective nsaid",
    "diclofenac": "nsaid",
    "thiocolchicoside": "muscle relaxant",
    "methyl salicylate": "topical salicylate",
    "menthol": "topical counterirritant",
    "linseed oil": "topical emollient",
    "insulin glargine": "long-acting insulin",
    "teriparatide": "parathyroid hormone analogue",
    "glimepiride": "sulfonylurea",
    "metformin": "biguanide",
    "pioglitazone": "thiazolidinedione",
    "teneligliptin": "dpp-4 inhibitor",
    "erythropoietin": "erythropoiesis-stimulating agent",
    "darbepoetin alfa": "erythropoiesis-stimulating agent",
    "tacrolimus": "calcineurin inhibitor immunosuppressant",
    "mycophenolate mofetil": "antimetabolite immunosuppressant",
    "mycophenolate sodium": "antimetabolite immunosuppressant",
    "dicyclomine": "anticholinergic antispasmodic",
    "tramadol": "opioid analgesic",
    "acetaminophen": "analgesic/antipyretic",
    "dexamethasone": "corticosteroid",
    "dexamethasone sodium phosphate": "corticosteroid",
    "betamethasone": "corticosteroid",
    "boswellia serrata extract": "herbal anti-inflammatory",
    "undenatured type ii collagen": "nutraceutical",
}


@dataclass
class PairReasoning:
    overall_assessment: str
    benefit_signal: str
    interaction_signal: str
    toxicity_signal: str
    evidence_strength: str
    interaction_class: str
    confidence: int
    why_bullets: List[str] = field(default_factory=list)
    interaction_findings: List[str] = field(default_factory=list)
    toxicity_findings: List[str] = field(default_factory=list)
    overlapping_adverse_effects: List[str] = field(default_factory=list)
    organ_concerns: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    contradictory_evidence: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)
    mechanism_summary: str = ""


# ---------------------------------------------------------------------------
# Curated demonstration reasoning for the leadership demo cases.
# Keys are frozensets of drug-class strings so brand/dose variants all match.
# ---------------------------------------------------------------------------
def _key(*classes: str) -> frozenset:
    return frozenset(classes)


CURATED: Dict[frozenset, PairReasoning] = {
    # CASE-001 EMROK + GLIMADAY — fluoroquinolone + sulfonylurea/biguanide
    _key("fluoroquinolone antibacterial", "sulfonylurea"): PairReasoning(
        overall_assessment="Potential Concern",
        benefit_signal="Low",
        interaction_signal="Moderate",
        toxicity_signal="Moderate",
        evidence_strength="Moderate",
        interaction_class="Pharmacodynamic interaction",
        confidence=68,
        why_bullets=[
            "Fluoroquinolone-class antibacterials have a recognised class association with dysglycaemia (both hypo- and hyperglycaemia).",
            "Sulfonylureas independently carry hypoglycaemia risk; co-exposure warrants glucose monitoring as a demonstration consideration.",
            "This is a demonstration heuristic from drug-class knowledge, not a retrieved finding for this specific product pair.",
        ],
        interaction_findings=[
            "Possible additive/pharmacodynamic effect on glucose homeostasis (demonstration heuristic).",
        ],
        toxicity_findings=[
            "Dysglycaemia is the primary overlapping consideration to monitor.",
        ],
        overlapping_adverse_effects=["dysglycaemia"],
        organ_concerns=["glucose metabolism"],
        supporting_evidence=[
            "Fluoroquinolone dysglycaemia is a documented class-level labelling consideration (demonstration heuristic).",
        ],
        evidence_gaps=[
            "No specific combination study for levonadifloxacin with this antidiabetic pair was retrieved in demo mode.",
        ],
        mechanism_summary="Potential additive disturbance of glucose regulation.",
    ),
    # CASE-002 Tacrolimus + Mycophenolate — established transplant regimen
    _key("calcineurin inhibitor immunosuppressant", "antimetabolite immunosuppressant"): PairReasoning(
        overall_assessment="Potentially Beneficial",
        benefit_signal="Moderate",
        interaction_signal="Moderate",
        toxicity_signal="Moderate",
        evidence_strength="Moderate",
        interaction_class="Additive effect",
        confidence=72,
        why_bullets=[
            "Calcineurin-inhibitor plus antimetabolite is a well-established combined immunosuppression strategy in transplantation.",
            "Additive immunosuppression raises overlapping infection and myelosuppression considerations.",
            "Established combined use does not remove the need for exposure monitoring; presented as a demonstration heuristic.",
        ],
        interaction_findings=[
            "Additive immunosuppressive effect is the expected pharmacodynamic interaction.",
        ],
        toxicity_findings=[
            "Overlapping infection risk and marrow suppression are the primary safety considerations.",
        ],
        overlapping_adverse_effects=["increased infection risk", "myelosuppression"],
        organ_concerns=["immune system", "bone marrow", "kidney (calcineurin nephrotoxicity)"],
        supporting_evidence=[
            "Combined immunosuppression is an established therapeutic pattern (demonstration heuristic).",
        ],
        evidence_gaps=[
            "Product-specific exposure and outcome data were not retrieved in demo mode.",
        ],
        mechanism_summary="Complementary immunosuppression via distinct mechanisms.",
    ),
    # CASE-004 Insulin glargine + Metformin/Sulfonylurea — established glycaemic control
    _key("long-acting insulin", "biguanide", "sulfonylurea"): PairReasoning(
        overall_assessment="Potentially Beneficial",
        benefit_signal="Moderate",
        interaction_signal="Moderate",
        toxicity_signal="Moderate",
        evidence_strength="Moderate",
        interaction_class="Additive effect",
        confidence=70,
        why_bullets=[
            "Basal insulin combined with oral antidiabetics is an established multi-agent glycaemic-control strategy.",
            "Additive glucose-lowering increases hypoglycaemia risk requiring monitoring.",
            "Presented as a demonstration heuristic distinguishing established therapy from a novel combination claim.",
        ],
        interaction_findings=["Additive glucose-lowering effect (pharmacodynamic)."],
        toxicity_findings=["Hypoglycaemia is the dominant overlapping safety signal."],
        overlapping_adverse_effects=["hypoglycaemia"],
        organ_concerns=["glucose metabolism"],
        supporting_evidence=[
            "Insulin plus oral antidiabetic co-therapy is an established pattern (demonstration heuristic).",
        ],
        evidence_gaps=["No product-specific outcome study retrieved in demo mode."],
        mechanism_summary="Additive glucose lowering across complementary mechanisms.",
    ),
    # CASE-005 Etoricoxib + (Dicyclomine/Tramadol/Acetaminophen)
    _key("cox-2 selective nsaid", "opioid analgesic", "analgesic/antipyretic", "anticholinergic antispasmodic"): PairReasoning(
        overall_assessment="Potential Concern",
        benefit_signal="Low",
        interaction_signal="Moderate",
        toxicity_signal="High",
        evidence_strength="Moderate",
        interaction_class="Additive effect",
        confidence=66,
        why_bullets=[
            "Stacking an NSAID with a multi-analgesic product raises overlapping GI, renal and hepatic considerations.",
            "Tramadol adds CNS depression and seizure/serotonergic considerations; cumulative acetaminophen exposure adds hepatic load.",
            "Demonstration heuristic highlighting overlapping toxicity domains, not a specific retrieved finding.",
        ],
        interaction_findings=[
            "Additive CNS depression (tramadol) and overlapping analgesic mechanisms.",
        ],
        toxicity_findings=[
            "Watch cumulative acetaminophen dose (hepatic) and NSAID GI/renal burden.",
            "Tramadol seizure threshold and serotonergic load are additional considerations.",
        ],
        overlapping_adverse_effects=["GI irritation", "hepatic load (acetaminophen)", "CNS depression"],
        organ_concerns=["gastrointestinal tract", "liver", "kidney", "central nervous system"],
        supporting_evidence=[
            "NSAID GI/renal risk and acetaminophen hepatotoxicity ceilings are established class facts (demonstration heuristic).",
        ],
        evidence_gaps=["No combined clinical safety study retrieved in demo mode."],
        mechanism_summary="Overlapping analgesic toxicity domains across several organs.",
    ),
    # CASE-003 (gabapentinoid + TCA + B12) + corticosteroid — limited combination evidence
    _key("gabapentinoid", "tricyclic antidepressant", "vitamin b12", "corticosteroid"): PairReasoning(
        overall_assessment="Insufficient Evidence",
        benefit_signal="Unknown",
        interaction_signal="Low",
        toxicity_signal="Moderate",
        evidence_strength="Low",
        interaction_class="Insufficient evidence",
        confidence=45,
        why_bullets=[
            "Gabapentinoid plus tricyclic contributes additive CNS/sedation considerations.",
            "Adding a systemic corticosteroid introduces separate metabolic/GI considerations rather than a defined interaction.",
            "Specific combination evidence is sparse; treated as Insufficient Evidence, not as reassurance of safety.",
        ],
        interaction_findings=["Additive sedation from gabapentinoid + tricyclic (demonstration heuristic)."],
        toxicity_findings=["Corticosteroid metabolic/GI effects are independent considerations."],
        overlapping_adverse_effects=["sedation/CNS depression"],
        organ_concerns=["central nervous system"],
        supporting_evidence=[],
        contradictory_evidence=[],
        evidence_gaps=[
            "No direct combination study retrieved for this specific multi-ingredient pairing in demo mode.",
        ],
        mechanism_summary="Partial additive CNS effect; overall combination poorly characterised.",
    ),
}


# ---------------------------------------------------------------------------
# Generic class-pair considerations for non-curated pairs (honest, qualitative)
# ---------------------------------------------------------------------------
GENERIC_CLASS_PAIR: Dict[frozenset, Dict[str, str]] = {
    _key("nsaid", "corticosteroid"): {
        "interaction": "Additive effect",
        "toxicity": "High",
        "note": "NSAID + corticosteroid co-exposure is a recognised GI-bleeding-risk consideration.",
        "organ": "gastrointestinal tract",
    },
    _key("cox-2 selective nsaid", "corticosteroid"): {
        "interaction": "Additive effect",
        "toxicity": "Moderate",
        "note": "Overlapping GI and renal considerations with corticosteroid co-exposure.",
        "organ": "gastrointestinal tract; kidney",
    },
    _key("opioid analgesic", "tricyclic antidepressant"): {
        "interaction": "Additive effect",
        "toxicity": "Moderate",
        "note": "Additive CNS depression and possible serotonergic considerations.",
        "organ": "central nervous system",
    },
    _key("sulfonylurea", "long-acting insulin"): {
        "interaction": "Additive effect",
        "toxicity": "Moderate",
        "note": "Additive glucose lowering increases hypoglycaemia risk.",
        "organ": "glucose metabolism",
    },
}


def classes_for(ingredients: List[str]) -> List[str]:
    out = []
    for ing in ingredients:
        cls = INGREDIENT_CLASS.get(ing.strip().lower())
        if cls and cls not in out:
            out.append(cls)
    return out


def reason_about_pair(
    ingredients_a: List[str], ingredients_b: List[str]
) -> Optional[PairReasoning]:
    """Return curated reasoning if the class fingerprint matches, else None."""
    classes = set(classes_for(ingredients_a) + classes_for(ingredients_b))
    # exact curated match: curated key must be a subset of the observed classes
    best: Optional[PairReasoning] = None
    best_overlap = 0
    for key, reasoning in CURATED.items():
        if key.issubset(classes):
            overlap = len(key)
            if overlap > best_overlap:
                best_overlap = overlap
                best = reasoning
    if best is not None:
        return best

    # generic class-pair heuristic
    classes_a = classes_for(ingredients_a)
    classes_b = classes_for(ingredients_b)
    for ca in classes_a:
        for cb in classes_b:
            hit = GENERIC_CLASS_PAIR.get(_key(ca, cb))
            if hit:
                return PairReasoning(
                    overall_assessment="Potential Concern",
                    benefit_signal="Low",
                    interaction_signal="Moderate",
                    toxicity_signal=hit["toxicity"],
                    evidence_strength="Low",
                    interaction_class=hit["interaction"],
                    confidence=55,
                    why_bullets=[
                        hit["note"],
                        "Demonstration heuristic from general drug-class knowledge; not a retrieved product-specific finding.",
                    ],
                    interaction_findings=[hit["note"]],
                    toxicity_findings=[hit["note"]],
                    organ_concerns=[hit["organ"]],
                    evidence_gaps=[
                        "No product-specific combination evidence retrieved in demo mode.",
                    ],
                    mechanism_summary=hit["note"],
                )
    return None
