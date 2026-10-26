"""Pre-collected offline evidence store.

Populated by ``precollect.py`` from real public APIs, then read at runtime so the
demo can run **fully offline** over genuine (not fabricated) evidence:

  * ``ingredient_identifiers.csv`` — RxNorm / PubChem CID per normalized ingredient
  * ``collected_evidence.json``    — real PubMed / openFDA items keyed by drug pair

Items loaded here are marked ``provenance_status="cached"`` and retain their
original source URL, identifier and retrieval date.
"""
from __future__ import annotations

import json
from typing import Dict, List

import pandas as pd

import config
from models.schemas import EvidenceItem


def pair_key(a: str, b: str) -> str:
    """Order-independent key for a drug pair."""
    return "|".join(sorted([a.strip().lower(), b.strip().lower()]))


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------
def load_identifiers() -> Dict[str, dict]:
    if not config.COLLECTED_IDENTIFIERS.exists():
        return {}
    df = pd.read_csv(config.COLLECTED_IDENTIFIERS, dtype=str, keep_default_na=False)
    out: Dict[str, dict] = {}
    for _, r in df.iterrows():
        key = str(r.get("normalized_name", "")).strip().lower()
        if key:
            out[key] = {
                "rxnorm": str(r.get("rxnorm_id", "")).strip(),
                "pubchem_cid": str(r.get("pubchem_cid", "")).strip(),
            }
    return out


def save_identifiers(rows: List[dict]) -> None:
    config.COLLECTED_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=["ingredient_name", "normalized_name", "rxnorm_id", "pubchem_cid"])
    df.to_csv(config.COLLECTED_IDENTIFIERS, index=False)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
def _load_raw_evidence() -> dict:
    if not config.COLLECTED_EVIDENCE.exists():
        return {}
    try:
        return json.loads(config.COLLECTED_EVIDENCE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def has_evidence(a: str, b: str) -> bool:
    return bool(_load_raw_evidence().get(pair_key(a, b)))


def load_evidence(a: str, b: str) -> List[EvidenceItem]:
    raw = _load_raw_evidence().get(pair_key(a, b), [])
    items: List[EvidenceItem] = []
    for it in raw:
        try:
            items.append(EvidenceItem(**it))
        except Exception:
            continue
    return items


def save_evidence(mapping: Dict[str, List[dict]]) -> None:
    config.COLLECTED_DIR.mkdir(parents=True, exist_ok=True)
    config.COLLECTED_EVIDENCE.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8"
    )
