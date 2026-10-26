"""Adapters for controlled public evidence sources (spec §13).

Design rules honoured here:
  * retry with exponential backoff
  * simple on-disk response caching
  * store source IDs and retrieval timestamps
  * handle 404 / no-result cases without fabricating data
  * never scrape aggressively; APIs only

These adapters require no API keys for basic use. They are only invoked when
the user enables live retrieval; the demo works fully offline without them.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import date
from pathlib import Path
from typing import List, Optional

import config

logger = logging.getLogger(__name__)


def _cache_path(key: str) -> Path:
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return config.CACHE_DIR / f"{digest}.json"


def _cached_get(key: str):
    path = _cache_path(key)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _cache_set(key: str, value) -> None:
    try:
        _cache_path(key).write_text(json.dumps(value), encoding="utf-8")
    except Exception:  # pragma: no cover
        pass


def _request_json(url: str, params: Optional[dict] = None) -> Optional[dict]:
    """GET JSON with retry/backoff and caching. Returns None on hard failure."""
    import requests

    cache_key = url + "?" + json.dumps(params or {}, sort_keys=True)
    cached = _cached_get(cache_key)
    if cached is not None:
        return cached

    delay = config.HTTP_BACKOFF_SECONDS
    for attempt in range(1, config.HTTP_MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=config.HTTP_TIMEOUT)
            if resp.status_code == 404:
                _cache_set(cache_key, {})  # cache empty result
                return {}
            if resp.status_code == 429 or resp.status_code >= 500:
                raise RuntimeError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data)
            return data
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Adapter request failed (attempt %s): %s", attempt, exc)
            if attempt == config.HTTP_MAX_RETRIES:
                return None
            time.sleep(delay)
            delay *= 2
    return None


def _today() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# PubChem PUG
# ---------------------------------------------------------------------------
def pubchem_cid(name: str) -> Optional[str]:
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{_quote(name)}/cids/JSON"
    )
    data = _request_json(url)
    if not data:
        return None
    ids = data.get("IdentifierList", {}).get("CID", [])
    return str(ids[0]) if ids else None


# ---------------------------------------------------------------------------
# NCBI E-utilities / PubMed
# ---------------------------------------------------------------------------
def pubmed_search(term: str, retmax: int = 5) -> List[str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": retmax,
        "tool": config.NCBI_TOOL,
    }
    if config.NCBI_EMAIL:
        params["email"] = config.NCBI_EMAIL
    data = _request_json(url, params)
    if not data:
        return []
    return data.get("esearchresult", {}).get("idlist", [])


def pubmed_summaries(pmids: List[str]) -> List[dict]:
    if not pmids:
        return []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "tool": config.NCBI_TOOL,
    }
    if config.NCBI_EMAIL:
        params["email"] = config.NCBI_EMAIL
    data = _request_json(url, params)
    if not data:
        return []
    result = data.get("result", {})
    out = []
    for pmid in result.get("uids", []):
        rec = result.get(pmid, {})
        out.append(
            {
                "pmid": pmid,
                "title": rec.get("title", ""),
                "source": rec.get("source", ""),
                "pubdate": rec.get("pubdate", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "retrieved_date": _today(),
            }
        )
    return out


# ---------------------------------------------------------------------------
# openFDA drug labeling
# ---------------------------------------------------------------------------
def openfda_label(term: str, limit: int = 1) -> List[dict]:
    url = "https://api.fda.gov/drug/label.json"
    params = {"search": f'openfda.generic_name:"{term}"', "limit": limit}
    data = _request_json(url, params)
    if not data:
        return []
    results = data.get("results", [])
    out = []
    for rec in results:
        openfda = rec.get("openfda", {})
        set_id = (rec.get("set_id") or (openfda.get("spl_set_id") or [""])[0])
        warnings = rec.get("warnings") or rec.get("drug_interactions") or []
        excerpt = warnings[0][:600] if warnings else "Label retrieved; see source."
        out.append(
            {
                "set_id": set_id,
                "brand_name": (openfda.get("brand_name") or [""])[0],
                "excerpt": excerpt,
                "url": (
                    f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={set_id}"
                    if set_id
                    else "https://open.fda.gov/apis/drug/label/"
                ),
                "retrieved_date": _today(),
            }
        )
    return out


# ---------------------------------------------------------------------------
# RxNorm normalization
# ---------------------------------------------------------------------------
def rxnorm_id(name: str) -> Optional[str]:
    url = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
    params = {"name": name}
    data = _request_json(url, params)
    if not data:
        return None
    ids = data.get("idGroup", {}).get("rxnormId", [])
    return str(ids[0]) if ids else None


# ---------------------------------------------------------------------------
# DailyMed (structured product labels)
# ---------------------------------------------------------------------------
def dailymed_spls(name: str, limit: int = 1) -> List[dict]:
    url = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
    params = {"drug_name": name, "pagesize": limit}
    data = _request_json(url, params)
    if not data:
        return []
    out = []
    for rec in data.get("data", [])[:limit]:
        set_id = rec.get("setid", "")
        out.append(
            {
                "set_id": set_id,
                "title": rec.get("title", ""),
                "url": f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={set_id}",
                "retrieved_date": _today(),
            }
        )
    return out


def _quote(text: str) -> str:
    import requests

    return requests.utils.quote(text)
