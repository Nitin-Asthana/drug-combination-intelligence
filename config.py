"""Central configuration for the Drug Combination Intelligence demo.

No secrets are stored here. Azure access uses Microsoft Entra ID via
``DefaultAzureCredential`` (run ``az login`` first). All tunables come from
environment variables, optionally loaded from a local ``.env`` file.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent

# The supplied data package is nested two levels deep. Point at it directly so
# the authoritative CSVs are never duplicated.
DATA_ROOT = (
    PROJECT_ROOT
    / "drug_combination_intelligence_data"
    / "drug_combination_intelligence_data"
)

# Allow an override (e.g. if the data package is relocated).
if os.getenv("DCI_DATA_ROOT"):
    DATA_ROOT = Path(os.environ["DCI_DATA_ROOT"]).resolve()

DRUG_MASTER = DATA_ROOT / "company" / "company_drug_master.csv"
INGREDIENT_MASTER = DATA_ROOT / "company" / "company_ingredient_master.csv"
INTERNAL_COMBINATION_RESEARCH = DATA_ROOT / "internal" / "internal_combination_research.csv"
DEMO_CASE_LIBRARY = DATA_ROOT / "internal" / "demo_case_library.csv"
PUBLIC_SOURCE_REGISTRY = DATA_ROOT / "public" / "public_source_registry.csv"
PUBLIC_EVIDENCE_RECIPES = DATA_ROOT / "public" / "public_evidence_collection_recipes.csv"
SOURCE_MANIFEST = DATA_ROOT / "metadata" / "source_manifest.csv"

CACHE_DIR = PROJECT_ROOT / ".cache"

# Pre-collected, inspectable evidence store (populated by precollect.py) so the
# demo can run fully offline over *real* retrieved identifiers/evidence.
COLLECTED_DIR = PROJECT_ROOT / "collected"
COLLECTED_IDENTIFIERS = COLLECTED_DIR / "ingredient_identifiers.csv"
COLLECTED_EVIDENCE = COLLECTED_DIR / "collected_evidence.json"

# ---------------------------------------------------------------------------
# Azure OpenAI / Azure AI Foundry (identity-based auth only)
# ---------------------------------------------------------------------------
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
AZURE_OPENAI_API_VERSION = os.getenv(
    "AZURE_OPENAI_API_VERSION", "2024-08-01-preview"
).strip()
# Cognitive Services scope used for Entra ID token exchange.
AZURE_OPENAI_SCOPE = os.getenv(
    "AZURE_OPENAI_SCOPE", "https://cognitiveservices.azure.com/.default"
).strip()
# Reasoning effort for gpt-5 / o-series models (minimal|low|medium|high).
# "low" keeps the leadership demo responsive. Empty disables the parameter.
AZURE_OPENAI_REASONING_EFFORT = os.getenv("AZURE_OPENAI_REASONING_EFFORT", "low").strip()
# Upper bound on generated tokens (includes reasoning tokens for gpt-5/o-series).
AZURE_OPENAI_MAX_TOKENS = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "3500"))

# ---------------------------------------------------------------------------
# Public API adapters
# ---------------------------------------------------------------------------
# Live retrieval is OFF by default so the leadership demo is deterministic and
# works fully offline. The UI exposes a toggle; this env var sets the default.
ENABLE_LIVE_RETRIEVAL = os.getenv("DCI_ENABLE_LIVE_RETRIEVAL", "false").lower() in (
    "1",
    "true",
    "yes",
)
HTTP_TIMEOUT = int(os.getenv("DCI_HTTP_TIMEOUT", "20"))
HTTP_MAX_RETRIES = int(os.getenv("DCI_HTTP_MAX_RETRIES", "3"))
HTTP_BACKOFF_SECONDS = float(os.getenv("DCI_HTTP_BACKOFF_SECONDS", "1.0"))
# Optional contact email recommended by NCBI E-utilities etiquette.
NCBI_TOOL = os.getenv("DCI_NCBI_TOOL", "drug-combination-intelligence-demo")
NCBI_EMAIL = os.getenv("DCI_NCBI_EMAIL", "").strip()

# ---------------------------------------------------------------------------
# Branding / copy
# ---------------------------------------------------------------------------
APP_TITLE = "Drug Interaction & Toxicity Analysis Agent"
APP_TAGLINE = "Accelerate evidence discovery and synthesis, while keeping researchers in control."
ORG_NAME = "Acme Pharma"

NON_CLINICAL_DISCLAIMER = (
    "Research evidence-synthesis demonstrator only. This tool is **not** a clinical "
    "decision-support system. It does not prescribe treatment, approve combinations, "
    "or claim clinical efficacy. Researcher review is required before any scientific "
    "or clinical decision."
)


def azure_openai_configured() -> bool:
    """True when the minimum Azure OpenAI settings are present."""
    return bool(AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT)
