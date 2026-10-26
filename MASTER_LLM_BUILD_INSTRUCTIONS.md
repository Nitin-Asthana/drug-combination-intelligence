# MASTER BUILD INSTRUCTIONS — AI DRUG COMBINATION INTELLIGENCE AGENT

Build a leadership-ready, lightweight enterprise web application called **Drug Combination Intelligence**.

## 1. Business purpose

The application demonstrates how an AI agent can accelerate early drug-combination research by combining:
1. organization/product knowledge,
2. synthetic internal research records for the demonstration,
3. authoritative public drug/safety information,
4. scientific literature,
5. public combination/synergy evidence.

The user asks a research question such as:

> Assess Drug/Product A + Drug/Product B for potential benefit, interaction, toxicity, evidence strength and evidence gaps.

The application must NOT present itself as a clinical decision-support system and must NOT prescribe treatment, approve a combination, or claim clinical efficacy. It is a research evidence synthesis demonstrator. Every conclusion must distinguish evidence from inference and show provenance.

## 2. Desired user journey

Keep the workflow intuitive and visible on one primary page:

SELECT COMBINATION
→ NORMALIZE DRUGS
→ SEARCH INTERNAL KNOWLEDGE
→ SEARCH PUBLIC COMBINATION EVIDENCE
→ SEARCH SAFETY / LABEL EVIDENCE
→ SEARCH SCIENTIFIC LITERATURE
→ ANALYZE INTERACTIONS
→ ANALYZE TOXICITY
→ SYNTHESIZE EVIDENCE
→ COMBINATION ASSESSMENT
→ HUMAN RESEARCHER REVIEW

Do not build a complicated multi-screen enterprise portal. The leadership demo should feel like one coherent research workbench.

## 3. Frontend

Use:
- Python 3.11+
- Streamlit
- pandas
- Plotly only where a simple visual materially helps
- light enterprise UI
- clean white/very-light-gray background
- blue/teal accents
- cards, badges, progress indicators
- responsive layout
- no dark theme
- no excessive animations

The main screen should have:
A. Header: "Drug Combination Intelligence"
B. Short value statement
C. Drug/Product A selector
D. Drug/Product B selector
E. Research question selector
F. "Analyze Combination" button
G. Agent workflow/progress panel
H. Combination Assessment card
I. Evidence cards
J. Evidence gaps / caveats
K. "View Evidence" expandable section
L. optional follow-up question box

## 4. Backend / agent architecture

Use a simple Python orchestration layer. Do not over-engineer.

Recommended modules:
- `app.py` — Streamlit UI
- `agents/identity_agent.py`
- `agents/internal_evidence_agent.py`
- `agents/public_evidence_agent.py`
- `agents/interaction_agent.py`
- `agents/toxicity_agent.py`
- `agents/evidence_synthesis_agent.py`
- `agents/assessment_agent.py`
- `services/source_adapters.py`
- `services/retrieval.py`
- `services/llm.py`
- `data/`
- `prompts/`

If a single-file implementation is required, keep the same logical separation as functions/classes inside the file.

## 5. Agents

### Agent 1 — Drug Identity Agent
Input: two product/drug names.

Responsibilities:
- map brand to active ingredient,
- normalize synonyms,
- identify dosage/form where available,
- retrieve RxNorm/PubChem identifiers when available,
- return canonical drug identities,
- never guess an identity.

Output:
- product_name
- canonical_ingredient
- aliases
- identifiers
- identity_confidence
- source references

### Agent 2 — Internal Evidence Agent
Search:
- `internal/internal_combination_research.csv`
- `company/company_drug_master.csv`
- any future authorized internal datasets.

Return:
- matching records,
- observed effects,
- toxicity signals,
- evidence strength,
- source/provenance.

IMPORTANT:
The included internal combination data is synthetic demo data. Display a visible "Synthetic demonstration data" provenance label.

### Agent 3 — Public Evidence Agent
Use controlled public sources:
- Manufacturer public product pages
- PubMed / NCBI
- PubChem
- DailyMed
- openFDA
- authorized combination datasets such as DrugComb, subject to licensing/terms
- LiverTox where relevant
- ChEMBL optionally for mechanism/target evidence.

Do not use unrestricted web search as the primary evidence mechanism. Prefer APIs and curated sources.

### Agent 4 — Interaction Agent
Analyze retrieved evidence for:
- known interaction,
- possible interaction,
- pharmacokinetic interaction,
- pharmacodynamic interaction,
- additive effect,
- antagonism,
- no interaction identified,
- insufficient evidence.

Never convert "no evidence found" into "safe".

### Agent 5 — Toxicity Agent
Look for:
- overlapping adverse effects,
- organ-specific toxicity,
- dose/exposure concerns,
- mechanism-based toxicity,
- label warnings,
- post-market safety signals,
- published toxicity findings.

For adverse-event databases, explicitly distinguish "reported signal" from "causal relationship".

### Agent 6 — Evidence Synthesis Agent
Compare:
- internal evidence,
- regulatory evidence,
- peer-reviewed literature,
- combination datasets,
- toxicity references.

Identify:
- supporting evidence,
- contradictory evidence,
- evidence gaps,
- source quality,
- recency,
- study context.

### Agent 7 — Assessment Agent
Return one of:
- Potentially Beneficial
- Potential Concern
- Potentially Toxic
- Neutral / No meaningful interaction identified
- Insufficient Evidence

Do NOT output "Approved", "Allowed", "Safe", "Effective", or a clinical recommendation.

Return:
- overall_assessment
- rationale
- benefit_signal
- interaction_signal
- toxicity_signal
- evidence_strength
- confidence
- evidence_gaps
- human_review_required
- citations

## 6. Assessment logic

The LLM must not invent numerical evidence.

If a source provides a quantitative synergy score, retain the actual source score and source.
If the source is qualitative, keep it qualitative.

Confidence is an AI synthesis confidence, not probability of clinical efficacy.

Suggested evidence weighting:
- official regulatory labeling: very high authority for label claims
- peer-reviewed primary study: high
- curated scientific database: high/moderate
- internal synthetic demo data: demonstration-only
- secondary websites: lower
- unverified web content: do not use as authoritative evidence

The system should prefer multiple independent sources over one source.

## 7. RAG design

For the demo, a simple hybrid retrieval approach is sufficient.

Structured retrieval:
- pandas/SQLite filtering for exact drug/ingredient matches.

Semantic retrieval:
- Azure AI Search or a lightweight local vector store if available.

Recommended production Azure architecture:
- Azure OpenAI for reasoning/synthesis
- Azure AI Search for RAG
- Azure Storage for raw/curated evidence
- Azure Functions or Container Apps for ingestion jobs
- Application Insights for telemetry

For the local demo, do not require all Azure services. Use local CSV + optional Azure OpenAI.

## 8. Azure authentication

Do NOT put Azure OpenAI API keys into source code.

Prefer Microsoft Entra ID / Azure CLI authentication:
- user runs `az login`
- Python uses `DefaultAzureCredential`
- use Azure OpenAI/Azure AI Foundry supported identity-based authentication
- configuration should come from environment variables such as endpoint/deployment names, not secrets.

The app should have a graceful local fallback using deterministic demo data if the Azure model is unavailable.

## 9. Structured output

Use Pydantic.

Example schema:

class CombinationAssessment:
    drug_a: str
    drug_b: str
    overall_assessment: str
    benefit_signal: str
    interaction_signal: str
    toxicity_signal: str
    evidence_strength: str
    confidence: int
    rationale: str
    supporting_evidence: list
    contradictory_evidence: list
    evidence_gaps: list
    human_review_required: bool

Do not accept free-form model output where structured output is expected.

## 10. UI result

After analysis, show:

COMBINATION ASSESSMENT

Drug A + Drug B

[Potentially Beneficial]

Evidence Strength: Moderate / High
AI Synthesis Confidence: 86%
Toxicity Signal: Low / Moderate / High / Unknown

Then:

WHY?
2–4 concise evidence-backed bullets.

BENEFIT SIGNAL
...

INTERACTION SIGNAL
...

TOXICITY SIGNAL
...

EVIDENCE
Internal Research — N records
Regulatory / Label — N records
Published Literature — N records
Combination Evidence — N records

EVIDENCE GAPS
...

HUMAN REVIEW
"Researcher review required before any scientific or clinical decision."

## 11. Provenance

Every evidence item must include:
- source_name
- source_type
- source_url
- source_identifier (PMID, CID, label ID, etc. where applicable)
- retrieved_date
- evidence_excerpt_or_summary
- authority_level
- provenance_status

The UI should make citations clickable.

## 12. Data model

Use the supplied data package.

Key files:
- `company/company_drug_master.csv`
- `company/company_ingredient_master.csv`
- `internal/internal_combination_research.csv`
- `internal/demo_case_library.csv`
- `public/public_source_registry.csv`
- `public/public_evidence_collection_recipes.csv`
- `metadata/source_manifest.csv`

Add new public evidence only through a controlled ingestion process.

## 13. Public data collection

Implement adapters for:
- PubChem PUG
- NCBI E-utilities / PubMed
- openFDA
- DailyMed
- RxNorm

For each adapter:
- retry with exponential backoff,
- rate-limit requests,
- cache responses,
- store source IDs,
- store retrieval timestamps,
- never scrape aggressively,
- handle 404/no-result cases,
- log failures,
- do not fabricate missing data.

For DrugComb or any other external dataset:
- verify current access method and license before downloading,
- store version/date,
- retain source attribution,
- do not redistribute restricted data.

## 14. Safety / scientific guardrails

The system must:
- never give patient-specific medical advice,
- never recommend a drug combination for treatment,
- never call a combination "safe" solely because no evidence was found,
- never call an adverse-event report proof of causality,
- distinguish preclinical, clinical, regulatory and observational evidence,
- surface contradictory evidence,
- surface evidence gaps,
- clearly label synthetic demonstration records,
- require human research/scientific review.

## 15. Demo behavior

The app must work even with no external API keys.

Create deterministic demo scenarios:
1. A combination with supportive synthetic evidence.
2. A combination with conflicting evidence.
3. A combination with a toxicity concern.
4. A combination with insufficient evidence.

When running in demo mode, show:
"Demo mode — synthetic internal research records are being used."

When connected to Azure/public APIs, show:
"Evidence retrieval mode — sources retrieved at runtime."

## 16. Leadership narrative

The application should communicate this story without requiring a technical explanation:

Traditional:
Researcher → search many sources → read papers → compare evidence → synthesize → document conclusion

Agentic:
Research question → AI agents search multiple evidence layers → reconcile evidence → identify uncertainty → produce a traceable Combination Assessment → researcher reviews

The value proposition is:
"Accelerate evidence discovery and synthesis, while keeping researchers in control."

## 17. Do not overbuild

This is a leadership demonstration, not a production pharmacology platform.

Do NOT add:
- user management,
- complex workflow administration,
- patient records,
- EHR integration,
- real clinical recommendations,
- complicated dashboards,
- dozens of screens,
- unnecessary microservices.

Keep the application to one main screen plus expandable evidence details.

## 18. Acceptance criteria

The application is complete when:

1. User selects two drugs/products.
2. Agent normalizes their identities.
3. Internal records are searched.
4. Public evidence sources are queried or represented through cached demo evidence.
5. Agent workflow is visibly shown.
6. Interaction and toxicity evidence are separately assessed.
7. Evidence is synthesized.
8. A clear combination assessment is produced.
9. Supporting sources are visible.
10. Contradictions and evidence gaps are visible.
11. Synthetic data is explicitly labelled.
12. No secrets are embedded.
13. `az login` / Entra identity can be used for Azure model access.
14. App runs locally with `streamlit run app.py`.
15. App still works in deterministic demo mode without external credentials.
