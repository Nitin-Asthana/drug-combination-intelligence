"""Hybrid retrieval helpers (spec §7).

Structured retrieval over internal CSVs plus construction of public evidence
items. Public items are either:
  * live-retrieved via the source adapters (when the user enables it), or
  * represented as a transparent *retrieval plan* built from the authorised
    source registry and collection recipes (default demo behaviour).

No public scientific finding is fabricated. Planned items carry
``provenance_status="planned_not_retrieved"``.
"""
from __future__ import annotations

from datetime import date
from typing import List

import pandas as pd

from models.schemas import EvidenceItem
from services import data_access as da
from services import source_adapters as adapters


def _today() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Internal (synthetic) evidence
# ---------------------------------------------------------------------------
def _pair_matches(rec_a: str, rec_b: str, tokens_a: set, tokens_b: set) -> bool:
    """True only if the record's two drugs map to the two *selected* drugs.

    Prevents a single shared ingredient (e.g. levonadifloxacin paired with a
    placeholder 'Drug X') from being counted as combination evidence for an
    unrelated selected pair.
    """
    rec_a = rec_a.strip().lower()
    rec_b = rec_b.strip().lower()
    return (rec_a in tokens_a and rec_b in tokens_b) or (
        rec_a in tokens_b and rec_b in tokens_a
    )


def search_internal(ingredients_a: List[str], ingredients_b: List[str]) -> List[EvidenceItem]:
    """Match synthetic internal combination records to the *selected pair*.

    Requires BOTH drugs in a record to correspond to the two selected drugs, so
    records pairing one real ingredient with a placeholder research compound
    (Drug X/Y/Z/…) are not surfaced as evidence for this specific combination.
    """
    df = da.internal_research()
    tokens_a = {i.strip().lower() for i in ingredients_a if i.strip()}
    tokens_b = {i.strip().lower() for i in ingredients_b if i.strip()}
    items: List[EvidenceItem] = []
    for _, row in df.iterrows():
        da_name = str(row.get("drug_a", "")).strip().lower()
        db_name = str(row.get("drug_b", "")).strip().lower()
        if _pair_matches(da_name, db_name, tokens_a, tokens_b):
            summary = (
                f"{row.get('combination_context', '')}: {row.get('observed_effect', '')} "
                f"(effect: {row.get('effect_category', '')}, toxicity: {row.get('toxicity_signal', '')}, "
                f"strength: {row.get('evidence_strength', '')})."
            )
            items.append(
                EvidenceItem(
                    source_name="Internal combination research (synthetic)",
                    source_type="internal_synthetic",
                    source_identifier=str(row.get("internal_evidence_id", "")),
                    retrieved_date=str(row.get("source_reference", "")) or _today(),
                    evidence_excerpt_or_summary=summary,
                    authority_level="Internal synthetic demo data",
                    provenance_status="synthetic",
                    evidence_layer="internal",
                )
            )
    return items


# ---------------------------------------------------------------------------
# Public evidence — retrieval plan (default) or live retrieval
# ---------------------------------------------------------------------------
def build_public_plan(ingredient_a: str, ingredient_b: str) -> List[EvidenceItem]:
    """Transparent, honest retrieval plan from the source registry + recipes.

    These items describe *what would be queried* and are clearly marked as not
    retrieved at runtime, so no finding is fabricated.
    """
    registry = da.source_registry()
    recipes = da.evidence_recipes()
    items: List[EvidenceItem] = []
    for _, rec in recipes.iterrows():
        template = str(rec.get("query_template", ""))
        query = template.replace("{A}", ingredient_a).replace("{B}", ingredient_b)
        preferred = str(rec.get("preferred_source", ""))
        reg_row = registry[registry["source_name"].str.contains(preferred, case=False, na=False)]
        url = reg_row.iloc[0]["source_url"] if not reg_row.empty else ""
        authority = reg_row.iloc[0]["authority_level"] if not reg_row.empty else "High"
        layer = _recipe_layer(str(rec.get("evidence_type", "")))
        items.append(
            EvidenceItem(
                source_name=f"{preferred} — {rec.get('evidence_type', '')}",
                source_type="retrieval_plan",
                source_url=url,
                source_identifier=str(rec.get("evidence_seed_id", "")),
                evidence_excerpt_or_summary=f"Planned query: {query}. {rec.get('agent_instruction', '')}",
                authority_level=str(authority),
                provenance_status="planned_not_retrieved",
                evidence_layer=layer,
            )
        )
    return items


def _recipe_layer(evidence_type: str) -> str:
    et = evidence_type.lower()
    if "toxicity" in et or "adverse" in et:
        return "toxicity"
    if "label" in et or "regulatory" in et or "fda" in et:
        return "regulatory"
    if "combination" in et or "efficacy" in et:
        return "combination"
    if "identity" in et:
        return "identity"
    return "literature"


def live_public_retrieval(ingredient_a: str, ingredient_b: str) -> List[EvidenceItem]:
    """Attempt real retrieval via public APIs. Returns whatever is found.

    Never fabricates; on failure/no-result the list is simply shorter.
    """
    items: List[EvidenceItem] = []

    # --- PubMed: exact pair literature ---
    pair_term = f"{ingredient_a} AND {ingredient_b}"
    pmids = adapters.pubmed_search(pair_term, retmax=5)
    for summary in adapters.pubmed_summaries(pmids):
        items.append(
            EvidenceItem(
                source_name="PubMed / NCBI",
                source_type="literature",
                source_url=summary["url"],
                source_identifier=f"PMID:{summary['pmid']}",
                retrieved_date=summary["retrieved_date"],
                evidence_excerpt_or_summary=f"{summary['title']} — {summary['source']} ({summary['pubdate']})",
                authority_level="Peer-reviewed primary study",
                provenance_status="retrieved",
                evidence_layer="literature",
            )
        )

    # --- openFDA labels for each ingredient (regulatory / toxicity) ---
    for ing in (ingredient_a, ingredient_b):
        for label in adapters.openfda_label(ing, limit=1):
            items.append(
                EvidenceItem(
                    source_name="openFDA Drug Labeling",
                    source_type="regulatory_label",
                    source_url=label["url"],
                    source_identifier=f"SPL:{label['set_id']}",
                    retrieved_date=label["retrieved_date"],
                    evidence_excerpt_or_summary=(
                        f"{ing} label excerpt: {label['excerpt']}"
                    ),
                    authority_level="Official regulatory labeling",
                    provenance_status="retrieved",
                    evidence_layer="regulatory",
                )
            )

    return items
