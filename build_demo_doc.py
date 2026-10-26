"""Generate the demo guide as a Word (.docx) document.

Usage:  python -m build_demo_doc
Produces:  DEMO_GUIDE.docx
"""
from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

import config

BLUE = RGBColor(0x0F, 0x6C, 0xBD)
TEAL = RGBColor(0x12, 0xA4, 0xA4)
GREEN = RGBColor(0x1F, 0x9D, 0x55)
ORANGE = RGBColor(0xD9, 0x83, 0x24)
PURPLE = RGBColor(0x6C, 0x5C, 0xE7)


def _shade(cell, hex_color: str) -> None:
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _glossary_group(doc, title, entries):
    h = doc.add_heading(title, level=2)
    for r in h.runs:
        r.font.color.rgb = BLUE
    for term, definition in entries:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(f"{term} — ").bold = True
        p.add_run(definition)


def _add_glossary(doc):
    doc.add_heading("9. Appendix — glossary of terms", level=1)
    doc.add_paragraph(
        "Plain-language meaning of every concept shown in the app, so anyone can read "
        "an assessment confidently."
    )

    _glossary_group(doc, "Overall assessment (the verdict)", [
        ("Potentially Beneficial", "Evidence and/or drug-class reasoning suggest the combination may add value. It is NOT a clinical endorsement or approval."),
        ("Potential Concern", "Signals suggest caution — an interaction and/or toxicity that warrants researcher review."),
        ("Potentially Toxic", "Overlapping or serious harm signals dominate; treat with particular caution."),
        ("Neutral / No meaningful interaction identified", "No material interaction was found between the two drugs."),
        ("Insufficient Evidence", "Not enough evidence to take a position. Important: this NEVER means the combination is safe — only that evidence is lacking."),
    ])

    _glossary_group(doc, "Signals (levels: None / Low / Moderate / High / Unknown)", [
        ("Benefit signal", "How strong the case is that the combination could have a positive/complementary effect."),
        ("Interaction signal", "How strong the evidence is that the two drugs affect each other's action or exposure."),
        ("Toxicity signal", "How strong the overlapping or combination-related harm considerations are."),
    ])

    _glossary_group(doc, "Interaction class", [
        ("Known interaction", "A well-established, documented interaction."),
        ("Possible interaction", "Plausible but not firmly established by the retrieved evidence."),
        ("Pharmacokinetic (PK) interaction", "One drug changes how the body absorbs, distributes, metabolises or clears the other (i.e. changes exposure/levels)."),
        ("Pharmacodynamic (PD) interaction", "The drugs act on the same or related pathways, changing the effect (not the levels)."),
        ("Additive effect", "Their effects add together (e.g. two agents both lowering glucose or both sedating)."),
        ("Antagonism", "One drug reduces or opposes the effect of the other."),
        ("No interaction identified", "No interaction was found in the evidence considered."),
        ("Insufficient evidence", "Not enough evidence to classify the interaction."),
    ])

    _glossary_group(doc, "Evidence strength (None / Low / Moderate / High)", [
        ("Meaning", "How authoritative and robust the underlying evidence is overall."),
        ("High", "Backed by official regulatory labeling and/or peer-reviewed primary studies."),
        ("Moderate", "Curated scientific databases or a mix of solid but limited sources."),
        ("Low", "Sparse, indirect, or synthetic demonstration data only."),
    ])

    _glossary_group(doc, "AI synthesis confidence (0–100%)", [
        ("What it is", "The AI's confidence that it reconciled the available evidence correctly and consistently."),
        ("What it is NOT", "It is NOT the probability of clinical efficacy or safety. High confidence on weak evidence still means weak evidence."),
    ])

    _glossary_group(doc, "Evidence layers (the counts on the Evidence tab)", [
        ("Internal research", "The organisation's own combination records. In this demo these are clearly-labelled SYNTHETIC demonstration records (not real research)."),
        ("Regulatory / label", "Official drug label content (openFDA / DailyMed) — high authority for label claims, interactions and warnings."),
        ("Published literature", "Peer-reviewed biomedical papers discovered via PubMed (title/citation metadata)."),
        ("Combination evidence", "Records/datasets specifically about the exact drug pair (e.g. a combination/synergy dataset such as DrugComb)."),
    ])

    _glossary_group(doc, "Internal vs external evidence", [
        ("Internal (combination) evidence", "Comes from within the organisation — here, synthetic internal research records. Carries demonstration-only weight."),
        ("External / public evidence", "Comes from authorised public sources (RxNorm, PubChem, PubMed, openFDA, DailyMed). Either retrieved live, pre-collected (cached), or shown as a planned query."),
    ])

    _glossary_group(doc, "Provenance status (how trustworthy each item is)", [
        ("synthetic", "Demonstration data — not real research or a real finding."),
        ("retrieved", "Fetched live from a public API during this run."),
        ("cached", "Real public evidence collected earlier and stored locally, served offline."),
        ("planned_not_retrieved", "A query the agent planned but did NOT execute — a search plan, not a finding. Never treated as evidence."),
        ("reference", "Product-master facts (e.g. the Acme Pharma product page composition)."),
    ])

    _glossary_group(doc, "Authority level (weighting of a source)", [
        ("Order used", "Official regulatory labeling > peer-reviewed primary study > curated scientific database > manufacturer public site > internal synthetic demo data / demonstration heuristic > secondary website."),
        ("Principle", "Multiple independent authoritative sources beat a single source; synthetic data never outweighs authoritative evidence."),
    ])

    _glossary_group(doc, "Identifiers you will see", [
        ("RxNorm ID", "A normalized drug-concept identifier from the U.S. National Library of Medicine."),
        ("PubChem CID", "A chemical compound identifier from NIH/PubChem."),
        ("PMID", "A PubMed article identifier for a specific paper."),
        ("SPL / SetID", "A Structured Product Label identifier (DailyMed / openFDA) for a specific drug label."),
    ])

    _glossary_group(doc, "Other key terms", [
        ("Normalization", "Mapping a brand product (e.g. EMROK) to its active ingredient(s) (levonadifloxacin) so evidence can be matched reliably."),
        ("Demonstration heuristic", "Reasoning derived from general drug-class pharmacology, clearly labelled as such — a starting hypothesis, not a retrieved finding."),
        ("Reported signal vs causal relationship", "An adverse-event report is a 'reported signal'. It is never, by itself, proof that the drug caused the event."),
        ("Evidence gaps", "What is missing (e.g. no pair-specific study) that would be needed to raise confidence."),
        ("Human review required", "A hard guardrail: a researcher must review before any scientific or clinical decision. The tool never decides."),
        ("Modes", "Deterministic demo = offline rule-based reasoning; AI synthesis (Azure) = gpt-5 reasoning over the evidence. Live retrieval on/off controls whether public APIs are queried at runtime."),
    ])


def _add_plain_english(doc):
    h = doc.add_heading("10. In plain English", level=1)
    doc.add_paragraph(
        "When scientists think about using two medicines together, they need to know three "
        "things: could the pair help, could the two drugs interfere with each other, and could "
        "they cause harm together. Answering that normally means hours of reading drug labels, "
        "research papers and databases. This application is an AI research assistant — an "
        "\u201cagent\u201d — that does that legwork in seconds. It works out exactly which "
        "ingredients are in each product, searches the company\u2019s own records and trusted "
        "public sources (drug labels, PubMed papers, chemical databases), and then pulls "
        "everything together into one clear, traceable answer."
    )
    doc.add_paragraph(
        "The point is not to replace the scientist, but to speed them up while keeping everything "
        "transparent. Every statement the agent makes shows where it came from — a real regulatory "
        "label, a published paper, or clearly-labelled demonstration data — and it always separates "
        "hard evidence from reasoning. It deliberately never says a combination is \u201csafe\u201d "
        "or \u201capproved\u201d; instead it points the researcher to the strongest evidence, "
        "highlights contradictions, and lists what is still missing. A human always makes the final "
        "call."
    )
    doc.add_paragraph(
        "Reading a result takes about five seconds. The headline verdict (for example "
        "\u201cPotential Concern\u201d) is the summary. The interaction signal says how likely the "
        "two drugs are to affect each other; the toxicity signal says how much overlapping harm to "
        "watch for; the benefit signal says whether there may be an upside. Evidence strength tells "
        "you how solid the underlying proof is, and AI confidence tells you how sure the AI is that "
        "it read that evidence correctly — not that the drug works. Put together, these let a leader "
        "see at a glance whether a combination deserves a closer human look, and exactly why."
    )


def build() -> str:
    doc = Document()

    # base font
    style = doc.styles["Normal"]
    style.font.name = "Segoe UI"
    style.font.size = Pt(10.5)

    # Title
    title = doc.add_heading("Drug Combination Intelligence", level=0)
    for run in title.runs:
        run.font.color.rgb = BLUE
    sub = doc.add_paragraph("Demo Guide — learn & showcase")
    sub.runs[0].italic = True
    sub.runs[0].font.color.rgb = TEAL
    doc.add_paragraph(
        "A short, self-contained script to demonstrate the app to leadership. "
        "Everything below runs fully offline over real, pre-collected evidence."
    )

    # 1. Setup
    doc.add_heading("1. One-time setup (already done on this machine)", level=1)
    doc.add_paragraph(
        "Dependencies live in a short-path virtual environment (outside OneDrive) "
        "and real evidence is already collected into the .\\collected folder."
    )
    doc.add_paragraph("On a fresh machine only:")
    for line in [
        "python -m venv C:\\dci_venv",
        "C:\\dci_venv\\Scripts\\python.exe -m pip install -r requirements.txt",
        "C:\\dci_venv\\Scripts\\python.exe -m precollect   (one time, needs internet)",
    ]:
        p = doc.add_paragraph(line)
        p.style = doc.styles["No Spacing"]
        p.runs[0].font.name = "Consolas"
        p.runs[0].font.size = Pt(9.5)

    # 2. Start
    doc.add_heading("2. Start the app (every time)", level=1)
    for line in [
        'cd path\\to\\drug-combination-intelligence',
        "C:\\dci_venv\\Scripts\\python.exe -m streamlit run app.py",
    ]:
        p = doc.add_paragraph(line)
        p.style = doc.styles["No Spacing"]
        p.runs[0].font.name = "Consolas"
        p.runs[0].font.size = Pt(9.5)
    doc.add_paragraph(
        "It opens at http://localhost:8501. No internet needed — it reads the stored "
        "collected/ evidence."
    )
    p = doc.add_paragraph()
    p.add_run("Optional live AI: ").bold = True
    p.add_run(
        "the Azure model (gpt-5.4) is already configured. Run 'az login' once and the "
        "app auto-switches to Azure synthesis. Set DCI_ENABLE_LIVE_RETRIEVAL=true in .env "
        "for fresh (non-cached) evidence."
    )

    # 3. The loop
    doc.add_heading("3. How to run one analysis (the 30-second loop)", level=1)
    for i, step in enumerate(
        [
            "In the sidebar, pick a Leadership demo case preset (fills both drugs + the question), or choose Drug/Product A and B manually.",
            "Click 'Analyze Combination'.",
            "Watch the agent workflow run step by step (normalize → search → analyze → synthesize → assess).",
            "Read the Combination Assessment badge + signal chips.",
            "Expand 'View Evidence' to show clickable, real citations (PubMed / openFDA).",
            "Point at Evidence gaps and 'Human review required' — the honesty story.",
        ],
        start=1,
    ):
        doc.add_paragraph(f"{i}. {step}", style="List Number")

    # 4. How the workflow works
    doc.add_heading("4. How the agentic workflow works", level=1)
    doc.add_paragraph(
        "When you click 'Analyze Combination', an orchestrator runs seven agents in "
        "sequence. Each agent adds to a shared, traceable context. The same pipeline "
        "runs offline (deterministic rules) or with Azure OpenAI (gpt-5.4)."
    )
    steps = [
        ("1. Drug Identity Agent",
         "Maps each product to its active ingredient(s) from the Acme Pharma product master, "
         "normalizes names, and attaches real RxNorm / PubChem identifiers. Never guesses.",
         "Example: TACLORAN 1 MG 10C → tacrolimus (RxNorm 42316, PubChem CID 445643); "
         "MYCORAL M → mycophenolate mofetil (RxNorm 68149, CID 5281078). GLIMADAY 2 mg is "
         "split into two ingredients: metformin + glimepiride."),
        ("2. Internal Evidence Agent",
         "Searches the synthetic internal research dataset. Requires BOTH drugs in a record "
         "to match your selected pair, so unrelated placeholder combinations are not surfaced.",
         "Example: EMROK + GABAWOK NT returns 0 internal records. The synthetic file only pairs "
         "levonadifloxacin with placeholder 'Drug X / Drug Y' — not gabapentin/nortriptyline — so "
         "those records are correctly NOT shown as evidence for this pair."),
        ("3. Public Evidence Agent",
         "Uses controlled public sources. If live retrieval is on it queries PubMed / openFDA; "
         "otherwise it reads the pre-collected offline store (real, cached); otherwise it shows a "
         "transparent retrieval plan (a query, not a finding).",
         "Example: tacrolimus + mycophenolate mofetil (offline) loads 5 real PubMed citations "
         "(e.g. PMID:42602030) + 2 openFDA labels from the pre-collected store — no network. A "
         "non-collected pair instead lists ~9 planned queries marked 'planned_not_retrieved'."),
        ("4. Interaction Agent",
         "Classifies the interaction (known / possible / PK / PD / additive / antagonism / none / "
         "insufficient). Never turns 'no evidence' into 'no interaction'.",
         "Example: tacrolimus + mycophenolate mofetil → 'Additive effect' (two immunosuppressants). "
         "EMROK + GABAWOK NT, with no retrieved pair evidence → 'Insufficient evidence' — NOT "
         "'no interaction identified'."),
        ("5. Toxicity Agent",
         "Identifies overlapping / organ-specific toxicity, always separating a 'reported signal' "
         "from a 'causal relationship'.",
         "Example: ETOBRIX (etoricoxib) + DIPATRAM PLUS flags overlapping GI (NSAID), hepatic "
         "(cumulative acetaminophen) and CNS (tramadol) burdens → Toxicity: High. Any openFDA "
         "adverse-event count is labelled a 'reported signal', not proof of causation."),
        ("6. Evidence Synthesis Agent",
         "Reconciles the layers into supporting evidence, contradictions, gaps, source quality and "
         "recency, weighting authoritative sources above synthetic demo data.",
         "Example: tacrolimus + mycophenolate → Supporting: established transplant regimen + "
         "retrieved labels/literature; Gaps: product-specific exposure data not retrieved; Note: "
         "synthetic internal records carry demonstration-only weight."),
        ("7. Assessment Agent",
         "Produces the final traceable Combination Assessment, enforces the allowed labels, strips "
         "forbidden terms (safe / approved / effective), and always requires human review.",
         "Example: tacrolimus + mycophenolate mofetil → 'Potentially Beneficial', AI synthesis "
         "confidence 72%, Human review required. If the model ever wrote 'safe' or 'approved', "
         "that phrase is removed before display."),
    ]
    for name, desc, example in steps:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(name + " — ").bold = True
        p.add_run(desc)
        ex = doc.add_paragraph()
        ex.paragraph_format.left_indent = Pt(24)
        ex_run = ex.add_run(example)
        ex_run.italic = True
        ex_run.font.size = Pt(9.5)
        ex_run.font.color.rgb = TEAL

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("Two 'brains': ").bold = True
    p.add_run(
        "Offline mode uses deterministic rules + curated drug-class heuristics. Azure mode sends "
        "the gathered evidence to gpt-5.4, which returns structured, validated output and falls "
        "back to the deterministic result if anything fails."
    )
    p = doc.add_paragraph()
    p.add_run("Provenance labels you will see: ").bold = True
    p.add_run(
        "synthetic (demo data) · cached / retrieved (real public evidence) · "
        "planned_not_retrieved (a query that was planned but not executed — not a claim)."
    )
    p = doc.add_paragraph()
    p.add_run("Guardrails: ").bold = True
    p.add_run(
        "never 'safe' from absence of evidence; adverse-event reports are not proof of causality; "
        "synthetic data is always labelled; researcher review is always required."
    )

    # 5. Research questions it works on
    doc.add_heading("5. Research questions it works on", level=1)
    doc.add_paragraph(
        "Pick one from the 'Research question' dropdown (a preset also fills this in). "
        "The workflow is tuned for these framings:"
    )
    for rq in [
        "Assess this combination for potential benefit, interaction, toxicity, evidence strength and evidence gaps.",
        "Assess interaction, safety and published combination evidence.",
        "Assess available evidence and identify evidence gaps.",
        "Assess overlapping safety considerations and evidence.",
        "Distinguish established therapy from novel combination evidence.",
    ]:
        doc.add_paragraph(rq, style="List Bullet")
    p = doc.add_paragraph()
    p.add_run("Follow-up questions: ").bold = True
    p.add_run(
        "After an analysis you can ask a free-text follow-up (e.g. 'Which evidence gap should we "
        "close first?'). With Azure connected, gpt-5.4 answers grounded ONLY in the traced "
        "evidence and cites the sources it used."
    )

    # 6. Scenarios
    doc.add_heading("6. Scenarios to showcase", level=1)
    doc.add_paragraph(
        "Use these presets from the sidebar. Each teaches a different point. Scenarios 1, 4 and 5 "
        "currently carry the richest real retrieved evidence (PubMed + regulatory labels). "
        "Selecting a preset auto-fills a fitting research question; if you pick drugs manually, use "
        "the 'Research question to select' line below each scenario."
    )

    scenarios = [
        (
            "Scenario 1 — Established beneficial combination",
            "TACLORAN 1 MG 10C (tacrolimus) + MYCORAL M (mycophenolate mofetil)",
            "Potentially Beneficial · Evidence Strength Moderate · Toxicity Moderate",
            "~5 real PubMed papers + 2 openFDA labels",
            "A known transplant immunosuppression pairing. The agent confirms the combination "
            "is well-represented in the literature, but still flags overlapping infection / "
            "marrow-suppression toxicity — it doesn't rubber-stamp it as 'safe'.",
            "Best: 'Assess interaction, safety and published combination evidence.' (works well — "
            "5 PubMed papers + labels are retrieved). Also works: 'Distinguish established therapy "
            "from novel combination evidence.' and the general benefit/interaction/toxicity question.",
        ),
        (
            "Scenario 2 — Class-level interaction concern",
            "EMROK (levonadifloxacin) + GLIMADAY 2 mg (metformin + glimepiride)",
            "Potential Concern · Interaction Moderate · Toxicity Moderate",
            "Product labels + class heuristic",
            "An antibiotic meeting a diabetes regimen. The agent surfaces the fluoroquinolone-class "
            "dysglycaemia consideration and recommends glucose monitoring — clearly labelled as a "
            "demonstration heuristic.",
            "Best: 'Assess this combination for potential benefit, interaction, toxicity, evidence "
            "strength and evidence gaps.' Also works: 'Assess interaction, safety and published "
            "combination evidence.' and 'Assess overlapping safety considerations and evidence.'",
        ),
        (
            "Scenario 3 — Overlapping toxicity (multi-drug product)",
            "ETOBRIX 90 MG 10C (etoricoxib) + DIPATRAM PLUS (dicyclomine + tramadol + acetaminophen)",
            "Potential Concern · Toxicity HIGH",
            "Product labels + class heuristic",
            "Stacking an NSAID onto a multi-analgesic. The agent adds up the overlapping GI, hepatic "
            "(acetaminophen ceiling) and CNS (tramadol) burdens — the kind of cross-product toxicity a "
            "human might miss at a glance.",
            "Best: 'Assess overlapping safety considerations and evidence.' (works — highlights the "
            "stacked toxicity). Also works: the general benefit/interaction/toxicity question.",
        ),
        (
            "Scenario 4 — Established multi-agent therapy",
            "GLARITUS 100IU (insulin glargine) + GLIMADAY 2 mg (metformin + glimepiride)",
            "Potentially Beneficial · Toxicity Moderate (hypoglycaemia)",
            "Product labels + literature",
            "Basal insulin plus oral antidiabetics — established therapy. The agent distinguishes "
            "'established combined use' from a 'novel efficacy claim', and keeps the hypoglycaemia "
            "watch-out front and centre.",
            "Best: 'Distinguish established therapy from novel combination evidence.' Also works: "
            "'Assess overlapping safety considerations and evidence.' (hypoglycaemia) and the general "
            "benefit/interaction/toxicity question.",
        ),
        (
            "Scenario 5 — Insufficient evidence (the honesty guardrail)",
            "M 1500 NP (pregabalin + nortriptyline + methylcobalamin) + DECDAN 0.5 MG 10 TB (dexamethasone)",
            "Insufficient Evidence · low confidence",
            "Labels + literature, but no strong pair evidence",
            "There isn't strong combination-specific evidence here. Critically, the agent says "
            "'Insufficient Evidence' — it never converts 'no evidence' into 'safe'. It lists exactly "
            "what's missing so a researcher knows what to chase.",
            "Best: 'Assess available evidence and identify evidence gaps.' (works — foregrounds the "
            "gaps). Also works: the general benefit/interaction/toxicity question.",
        ),
        (
            "Scenario 6 — Provenance & guardrails deep-dive",
            "Any pair above → expand 'View Evidence'",
            "Traceable citations with authority levels",
            "synthetic / cached / planned_not_retrieved provenance",
            "Every line is traceable to a source with an authority level. Synthetic demo data is "
            "labelled as such; real PubMed/openFDA items are 'cached'; a query plan is "
            "'planned_not_retrieved' (not a claim). This is decision support with provenance, not a "
            "black box.",
            "Any question works — use the general 'Assess this combination for potential benefit, "
            "interaction, toxicity, evidence strength and evidence gaps.', then expand View Evidence.",
        ),
    ]

    for name, drugs, expected, evidence, say, questions in scenarios:
        h = doc.add_heading(name, level=2)
        for r in h.runs:
            r.font.color.rgb = BLUE
        p = doc.add_paragraph()
        p.add_run("Drugs: ").bold = True
        p.add_run(drugs)
        p = doc.add_paragraph()
        p.add_run("Research question to select: ").bold = True
        rq_run = p.add_run(questions)
        rq_run.font.size = Pt(9.5)
        rq_run.font.color.rgb = BLUE
        p = doc.add_paragraph()
        p.add_run("Expected: ").bold = True
        run = p.add_run(expected)
        run.font.color.rgb = (
            GREEN if "Beneficial" in expected else ORANGE if "Concern" in expected else PURPLE
        )
        p = doc.add_paragraph()
        p.add_run("Evidence: ").bold = True
        p.add_run(evidence)
        p = doc.add_paragraph()
        p.add_run("Say: ").bold = True
        say_run = p.add_run("\u201c" + say + "\u201d")
        say_run.italic = True

    # 7. Narrative
    doc.add_heading("7. The 60-second leadership narrative", level=1)
    p = doc.add_paragraph()
    p.add_run("Traditional: ").bold = True
    p.add_run(
        "a researcher searches many sources, reads papers, compares, synthesizes, and "
        "documents — hours per combination."
    )
    p = doc.add_paragraph()
    p.add_run("Agentic: ").bold = True
    p.add_run(
        "one research question → AI agents search internal + public evidence layers, "
        "reconcile them, flag contradictions and gaps, and produce a traceable Combination "
        "Assessment — in seconds — with the researcher kept firmly in control."
    )
    p = doc.add_paragraph()
    p.add_run("Value: ").bold = True
    vr = p.add_run(
        "Accelerate evidence discovery and synthesis, while keeping researchers in control."
    )
    vr.italic = True
    vr.font.color.rgb = TEAL

    # 8. Troubleshooting table
    doc.add_heading("8. If something goes wrong", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Symptom"
    hdr[1].text = "Fix"
    for c in hdr:
        for para in c.paragraphs:
            for r in para.runs:
                r.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _shade(c, "0F6CBD")
    rows = [
        ("streamlit: command not found", "Use full path: C:\\dci_venv\\Scripts\\python.exe -m streamlit run app.py"),
        ("Port 8501 busy", "Add --server.port 8788"),
        ("Re-verify everything", "C:\\dci_venv\\Scripts\\python.exe -m validate"),
        ("Evidence thin for a non-demo pair", "That pair wasn't pre-collected; enable live retrieval or extend precollect.py"),
    ]
    for a, b in rows:
        cells = table.add_row().cells
        cells[0].text = a
        cells[1].text = b

    # 9. Appendix — glossary
    _add_glossary(doc)

    # 10. In plain English
    _add_plain_english(doc)

    # Footer disclaimer
    doc.add_paragraph()
    disc = doc.add_paragraph()
    dr = disc.add_run(
        "Reminder: research evidence-synthesis demonstrator only — not a clinical "
        "decision-support system. Researcher review required before any decision."
    )
    dr.italic = True
    dr.font.size = Pt(9)
    dr.font.color.rgb = RGBColor(0x6B, 0x53, 0x00)

    out_path = config.PROJECT_ROOT / "DEMO_GUIDE.docx"
    try:
        doc.save(str(out_path))
    except PermissionError:
        # File is open (locked) in Word — save a timestamped copy instead.
        from datetime import datetime

        alt = config.PROJECT_ROOT / f"DEMO_GUIDE_{datetime.now():%H%M%S}.docx"
        doc.save(str(alt))
        return str(alt) + "  (original was locked/open in Word)"
    return str(out_path)


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
