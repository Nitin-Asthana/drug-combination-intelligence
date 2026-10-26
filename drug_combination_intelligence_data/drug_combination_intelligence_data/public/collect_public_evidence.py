"""
Public evidence collector skeleton.
This intentionally does not invent findings. It resolves identifiers and stores
source metadata; extend it with the official APIs and respect rate limits/licensing.
"""
import csv, time, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ING = ROOT / "company" / "company_ingredient_master.csv"

def pubchem_cid(name: str):
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/cids/JSON".format(
        requests.utils.quote(name)
    )
    r = requests.get(url, timeout=20)
    if r.ok:
        ids = r.json().get("IdentifierList", {}).get("CID", [])
        return ids[0] if ids else ""
    return ""

def pubmed_search(term: str, retmax=10):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db":"pubmed","term":term,"retmode":"json","retmax":retmax}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])

def openfda_label(term: str, limit=10):
    url = "https://api.fda.gov/drug/label.json"
    params = {"search":f'openfda.generic_name:"{term}"',"limit":limit}
    r = requests.get(url, params=params, timeout=20)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return r.json().get("results", [])

if __name__ == "__main__":
    print("Use this collector only against permitted public APIs.")
    print("Implement DailyMed, RxNorm and combination-dataset adapters similarly.")
