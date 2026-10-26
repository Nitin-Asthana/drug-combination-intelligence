"""Agent 1 — Drug Identity Agent (spec §5).

Maps a product name to canonical ingredient(s) using the ABC Pharma product and
ingredient masters. Optionally enriches identifiers via RxNorm/PubChem when live
retrieval is enabled. Never guesses an identity.
"""
from __future__ import annotations

from datetime import date

from agents.base import AgentContext
from models.schemas import DrugIdentity
from services import collected_store
from services import data_access as da
from services import source_adapters as adapters


def resolve_identity(product_name: str, live: bool) -> DrugIdentity:
    row = da.get_product_row(product_name)
    if not row:
        return DrugIdentity(
            product_name=product_name,
            identity_confidence="Unknown",
            resolved=False,
            note="Product not found in the ABC Pharma product master; identity not resolved.",
        )

    ingredients = da.split_ingredients(row.get("active_ingredient_text", ""))
    normalized = [da.normalized_ingredient(i) for i in ingredients]
    canonical = "; ".join(normalized) if normalized else row.get("active_ingredient_text", "")

    identifiers: dict = {}
    aliases = []
    collected_ids = collected_store.load_identifiers()
    for original, norm in zip(ingredients, normalized):
        ing_row = da.find_ingredient_row(original)
        if ing_row:
            if norm and norm.lower() != original.lower():
                aliases.append(f"{original} → {norm}")
            if ing_row.get("rxnorm_id"):
                identifiers.setdefault("rxnorm", {})[norm] = ing_row["rxnorm_id"]
            if ing_row.get("pubchem_cid"):
                identifiers.setdefault("pubchem_cid", {})[norm] = ing_row["pubchem_cid"]
        # Overlay pre-collected identifiers (offline, real) where available.
        collected = collected_ids.get((norm or original).strip().lower())
        if collected:
            if collected.get("rxnorm"):
                identifiers.setdefault("rxnorm", {})[norm] = collected["rxnorm"]
            if collected.get("pubchem_cid"):
                identifiers.setdefault("pubchem_cid", {})[norm] = collected["pubchem_cid"]

    # Optional live identifier enrichment (single-ingredient products only, to
    # keep API usage modest). Never fabricates: missing IDs stay missing.
    if live and len(normalized) == 1:
        name = normalized[0]
        cid = adapters.pubchem_cid(name)
        if cid:
            identifiers.setdefault("pubchem_cid", {})[name] = cid
        rx = adapters.rxnorm_id(name)
        if rx:
            identifiers.setdefault("rxnorm", {})[name] = rx

    confidence = "High" if normalized else "Low"

    return DrugIdentity(
        product_name=product_name,
        canonical_ingredient=canonical,
        aliases=aliases,
        identifiers=identifiers,
        dosage_form=row.get("dosage_form", ""),
        therapeutic_category=row.get("therapeutic_category", ""),
        composition=row.get("composition_as_published", ""),
        identity_confidence=confidence,
        source_references=[row.get("source_url", "")],
        resolved=bool(normalized),
        note="Ingredient(s) resolved from ABC Pharma product master.",
    )


def run(ctx: AgentContext) -> AgentContext:
    ctx.identity_a = resolve_identity(ctx.product_a, ctx.live_retrieval)
    ctx.identity_b = resolve_identity(ctx.product_b, ctx.live_retrieval)
    ctx.ingredients_a = da.all_normalized_ingredients_for_product(ctx.product_a)
    ctx.ingredients_b = da.all_normalized_ingredients_for_product(ctx.product_b)
    # add identity evidence provenance
    for identity in (ctx.identity_a, ctx.identity_b):
        if identity and identity.source_references:
            ctx.evidence.append(
                _identity_evidence(identity)
            )
    return ctx


def _identity_evidence(identity: DrugIdentity):
    from models.schemas import EvidenceItem

    return EvidenceItem(
        source_name="ABC Pharma Branded Products",
        source_type="product_master",
        source_url=identity.source_references[0] if identity.source_references else "",
        source_identifier=identity.product_name,
        retrieved_date=date.today().isoformat(),
        evidence_excerpt_or_summary=(
            f"{identity.product_name}: {identity.composition or identity.canonical_ingredient} "
            f"({identity.therapeutic_category}; {identity.dosage_form})."
        ),
        authority_level="Manufacturer public site",
        provenance_status="retrieved",
        evidence_layer="identity",
    )
