# Drug Combination Intelligence

A leadership-ready, lightweight research **evidence-synthesis demonstrator** that
shows how an AI agent workflow can accelerate early drug-combination research for
**Acme Pharma** products.

> ⚠️ **Not a clinical decision-support system.** It does not prescribe treatment,
> approve combinations, or claim clinical efficacy. Every conclusion distinguishes
> *evidence* from *inference*, shows provenance, and requires researcher review.

---

## What it does

The user selects two products and a research question. A visible agent workflow
then runs:

```
NORMALIZE DRUGS → SEARCH INTERNAL KNOWLEDGE → SEARCH PUBLIC EVIDENCE
→ ANALYZE INTERACTIONS → ANALYZE TOXICITY → SYNTHESIZE EVIDENCE
→ COMBINATION ASSESSMENT → HUMAN RESEARCHER REVIEW
```

and produces a traceable **Combination Assessment** (one of *Potentially
Beneficial / Potential Concern / Potentially Toxic / Neutral / Insufficient
Evidence*) with benefit, interaction and toxicity signals, supporting and
contradictory evidence, evidence gaps, and clickable citations.

---

## Quick start (deterministic demo — no keys required)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app runs fully offline using the supplied data package and a deterministic
demonstration reasoning engine. Synthetic internal records are clearly labelled.

---

## Optional: Azure OpenAI synthesis (Microsoft Entra ID — no API keys)

Secrets are **never** stored in code. Azure access uses identity-based auth.

```powershell
az login
# configure endpoint + deployment (identity, not keys)
copy .env.example .env
# edit .env:  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT
streamlit run app.py
```

The app uses `DefaultAzureCredential` to obtain a token for the Cognitive
Services scope and passes it to the Azure OpenAI SDK. If Azure is unavailable,
the app automatically falls back to deterministic demo mode.

### Optional: live public retrieval

Toggle **“Attempt live public retrieval”** in the sidebar to query public APIs
(PubMed / openFDA / PubChem / RxNorm). These require no API key. Adapters use
retry-with-backoff, response caching, and never fabricate missing data. Off by
default so the demo stays deterministic.

---

## Fully offline over *real* evidence (pre-collection)

The supplied CSVs contain product facts, **synthetic** internal records, and a
**source registry + query recipes** — they do **not** contain collected public
findings. To run offline over *genuine* evidence, pre-collect once (network
required), then run fully offline:

```powershell
# 1) fetch real identifiers + evidence into ./collected (one time, needs network)
python -m precollect

# 2) run fully offline over the cached real data  (.env: DCI_ENABLE_LIVE_RETRIEVAL=false)
streamlit run app.py
```

`precollect.py` writes:

- `collected/ingredient_identifiers.csv` — real RxNorm / PubChem CIDs per ingredient
- `collected/collected_evidence.json` — real PubMed citations + openFDA labels per demo pair

At runtime these load as evidence with `provenance_status="cached"`, so the app
shows genuine, clickable citations with **no network calls**. Nothing is
fabricated: pairs with no published literature simply show fewer items.

---

## Project structure

```
app.py                     Streamlit UI (single research workbench)
config.py                  Paths + identity-based Azure config (no secrets)
models/schemas.py          Pydantic structured-output contracts
prompts/                   System prompts per reasoning agent
agents/
  identity_agent.py        Agent 1 — normalize product → ingredient identity
  internal_evidence_agent  Agent 2 — search synthetic internal research
  public_evidence_agent    Agent 3 — controlled public sources / retrieval plan
  interaction_agent.py     Agent 4 — interaction analysis
  toxicity_agent.py        Agent 5 — toxicity analysis
  evidence_synthesis_agent Agent 6 — reconcile evidence layers
  assessment_agent.py      Agent 7 — final traceable assessment (guardrailed)
  orchestrator.py          Visible workflow orchestration
services/
  data_access.py           Structured access over the CSV data package
  source_adapters.py       PubChem / PubMed / openFDA / RxNorm / DailyMed
  retrieval.py             Hybrid retrieval (internal + public plan/live)
  reasoner.py              Deterministic reasoning core
  demo_knowledge.py        Curated demonstration heuristics
  llm.py                   Azure OpenAI via Entra ID (DefaultAzureCredential)
drug_combination_intelligence_data/   Supplied data package (authoritative)
```

---

## Data & provenance

- `company/` — product facts extracted from the public Acme Pharma India Branded
  Business page.
- `internal/` — **synthetic** combination research (demonstration only; never
  presented as real research or clinical evidence).
- `public/` — authorised source registry + repeatable collection recipes. No
  public finding is fabricated; planned queries are labelled
  `planned_not_retrieved` until actually retrieved.

Every evidence item carries: source name, source type, URL, identifier,
retrieval date, summary, authority level, and provenance status.

---

## Safety guardrails

- Never gives patient-specific medical advice or treatment recommendations.
- Never calls a combination "safe" because no evidence was found.
- Never treats an adverse-event report as proof of causality.
- Distinguishes preclinical / clinical / regulatory / observational evidence.
- Surfaces contradictions and evidence gaps.
- Labels synthetic demonstration records.
- Forbidden assessment terms (*approved / allowed / safe / effective /
  recommended*) are blocked in the Assessment Agent.

---

## Deterministic demo scenarios

Use the sidebar presets. The curated cases illustrate:

1. **Supportive** — established combined therapy (e.g. Tacrolimus + Mycophenolate).
2. **Concern / conflicting** — class-level interaction (e.g. fluoroquinolone + antidiabetic).
3. **Toxicity concern** — overlapping organ toxicity (e.g. NSAID + multi-analgesic).
4. **Insufficient evidence** — sparse combination evidence.

---

## Validate

```powershell
python -m validate
```

This runs the full pipeline across the demo cases in deterministic mode and
prints each assessment.
