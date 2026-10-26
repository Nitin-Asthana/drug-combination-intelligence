"""Pre-collect real public evidence for fully-offline demo runs.

Fetches, ONCE, from authorised public APIs (RxNorm, PubChem, PubMed, openFDA):
  * ingredient identifiers  -> collected/ingredient_identifiers.csv
  * pair evidence (labels + literature) -> collected/collected_evidence.json

After running this with network access, the app can run FULLY OFFLINE and still
show genuine (not fabricated) identifiers and citations — set
``DCI_ENABLE_LIVE_RETRIEVAL=false`` and the pipeline reads this store.

Usage:  python -m precollect
Requires network access. Respects the adapters' retry/backoff/caching. Never
fabricates: missing results are simply left blank.
"""
from __future__ import annotations

import sys
from datetime import date

from services import collected_store as store
from services import data_access as da
from services import source_adapters as adapters


def collect_identifiers() -> list:
    df = da.ingredient_master()
    rows = []
    print(f"Resolving identifiers for {len(df)} ingredients…")
    for _, r in df.iterrows():
        name = str(r.get("normalized_name") or r.get("ingredient_name", "")).strip()
        if not name:
            continue
        cid = adapters.pubchem_cid(name) or ""
        rx = adapters.rxnorm_id(name) or ""
        rows.append(
            {
                "ingredient_name": r.get("ingredient_name", ""),
                "normalized_name": name,
                "rxnorm_id": rx,
                "pubchem_cid": cid,
            }
        )
        print(f"  {name:<32} rxnorm={rx or '-':<8} pubchem={cid or '-'}")
    store.save_identifiers(rows)
    print(f"Saved {len(rows)} identifier rows.")
    return rows


def _evidence_for_pair(ing_a: str, ing_b: str) -> list:
    items = []

    # Literature (PubMed) for the exact pair
    pmids = adapters.pubmed_search(f"{ing_a} AND {ing_b}", retmax=5)
    for s in adapters.pubmed_summaries(pmids):
        items.append(
            {
                "source_name": "PubMed / NCBI",
                "source_type": "literature",
                "source_url": s["url"],
                "source_identifier": f"PMID:{s['pmid']}",
                "retrieved_date": s["retrieved_date"],
                "evidence_excerpt_or_summary": f"{s['title']} — {s['source']} ({s['pubdate']})",
                "authority_level": "Peer-reviewed primary study",
                "provenance_status": "cached",
                "evidence_layer": "literature",
            }
        )

    # Regulatory labels (openFDA) for each ingredient
    for ing in (ing_a, ing_b):
        for label in adapters.openfda_label(ing, limit=1):
            items.append(
                {
                    "source_name": "openFDA Drug Labeling",
                    "source_type": "regulatory_label",
                    "source_url": label["url"],
                    "source_identifier": f"SPL:{label['set_id']}",
                    "retrieved_date": label["retrieved_date"],
                    "evidence_excerpt_or_summary": f"{ing} label excerpt: {label['excerpt']}",
                    "authority_level": "Official regulatory labeling",
                    "provenance_status": "cached",
                    "evidence_layer": "regulatory",
                }
            )
    return items


def collect_pair_evidence() -> dict:
    cases = da.demo_cases()
    mapping: dict = {}
    print(f"\nCollecting evidence for {len(cases)} demo pairs…")
    for _, row in cases.iterrows():
        ing_a_list = da.all_normalized_ingredients_for_product(row["product_a"])
        ing_b_list = da.all_normalized_ingredients_for_product(row["product_b"])
        ing_a = ing_a_list[0] if ing_a_list else row["product_a"]
        ing_b = ing_b_list[0] if ing_b_list else row["product_b"]
        key = store.pair_key(ing_a, ing_b)
        items = _evidence_for_pair(ing_a, ing_b)
        mapping[key] = items
        print(f"  {row['product_a']} + {row['product_b']}  ({ing_a} | {ing_b}) -> {len(items)} item(s)")
    store.save_evidence(mapping)
    print(f"Saved evidence for {len(mapping)} pairs.")
    return mapping


def main() -> int:
    print(f"Pre-collection started {date.today().isoformat()} (network required).")
    try:
        collect_identifiers()
        collect_pair_evidence()
    except Exception as exc:  # pragma: no cover
        print(f"Pre-collection error: {exc}")
        return 1
    print("\nDone. Set DCI_ENABLE_LIVE_RETRIEVAL=false to run fully offline over this store.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
