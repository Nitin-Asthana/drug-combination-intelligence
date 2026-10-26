"""Drug Combination Intelligence — Streamlit research workbench (spec §3, §10).

Run with:  streamlit run app.py

Works fully offline in deterministic demo mode. When Azure OpenAI is configured
(endpoint + deployment) and `az login` has been run, the reasoning agents use
Azure via Microsoft Entra ID.
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import config
from agents import orchestrator
from agents.base import load_prompt
from models.schemas import AnalysisResult
from services import data_access as da
from services.llm import LLMUnavailable, get_llm

# ---------------------------------------------------------------------------
# Page setup + styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
/* App shell: soft page background + broad framed canvas */
.stApp {background: #eaeef3;}
.block-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    box-shadow: 0 10px 34px rgba(16,40,70,.10);
    padding: 1.8rem 2rem 2.6rem !important;
    margin-top: 1.2rem;
    max-width: 1280px;
}
h1, h2, h3, h4 {color: #0f2c47;}
.dci-hero {
    background: linear-gradient(120deg, #0b5aa2 0%, #0f6cbd 45%, #12a4a4 100%);
    color: #ffffff; padding: 1.5rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;
    box-shadow: 0 6px 20px rgba(15,108,189,.18);
}
.dci-hero h1 {color: #ffffff; margin: 0 0 .35rem 0; font-size: 1.6rem; letter-spacing:.2px;}
.dci-hero p {margin: 0; opacity: .95; font-size: .98rem;}
.dci-hero .dci-eyebrow {text-transform: uppercase; letter-spacing: 2px; font-size: .68rem; opacity:.85;}
.dci-badge {
    display: inline-block; padding: .4rem 1rem; border-radius: 999px;
    font-weight: 700; font-size: 1.02rem; color: #fff; letter-spacing:.2px;
}
.dci-chip {
    display: inline-block; padding: .18rem .6rem; border-radius: 6px;
    font-size: .78rem; font-weight: 600; margin: 0 .35rem .35rem 0;
}
.dci-pill {
    display:inline-block; padding:.2rem .7rem; border-radius:999px;
    font-size:.82rem; font-weight:700;
}
.dci-kpi-label {font-size:.72rem; text-transform:uppercase; letter-spacing:.6px; color:#6b7684; margin-bottom:.2rem;}
.dci-kpi-val {font-size:1.1rem; font-weight:800; line-height:1.25; white-space:normal; word-break:break-word;}
.dci-kpi {text-align:center;}
.dci-kpi .dci-kpi-val {min-height:2.5rem; display:flex; align-items:center; justify-content:center;}
.dci-drugs {font-size:1.15rem; font-weight:700; color:#0f2c47;}
.dci-prov {font-size:.74rem; color:#7a8493;}
.dci-review {
    background: #fff8e6; border: 1px solid #f2d98c; border-radius: 12px;
    padding: .85rem 1.1rem; color: #6b5300; font-size:.9rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important; border-color:#e6ebf1 !important;
    box-shadow: 0 1px 3px rgba(16,40,70,.05);
}
.stTabs [data-baseweb="tab-list"] {gap: 4px;}
.stTabs [data-baseweb="tab"] {font-weight:600;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
ASSESSMENT_COLORS = {
    "Potentially Beneficial": "#1f9d55",
    "Potential Concern": "#d98324",
    "Potentially Toxic": "#c0392b",
    "Neutral / No meaningful interaction identified": "#5b6675",
    "Insufficient Evidence": "#6c5ce7",
}
SIGNAL_COLORS = {
    "None": "#9aa4b2",
    "Low": "#1f9d55",
    "Moderate": "#d98324",
    "High": "#c0392b",
    "Unknown": "#6c5ce7",
}
PROVENANCE_COLORS = {
    "synthetic": "#6c5ce7",
    "cached": "#1f9d55",
    "retrieved": "#1f9d55",
    "planned_not_retrieved": "#9aa4b2",
    "reference": "#0f6cbd",
    "demonstration": "#6c5ce7",
}


def prov_color(status: str) -> str:
    return PROVENANCE_COLORS.get(status, "#5b6675")


def badge(text: str, color: str) -> str:
    return f'<span class="dci-badge" style="background:{color}">{text}</span>'


def pill(value: str, color: str) -> str:
    return (
        f'<span class="dci-pill" style="background:{color}1a;color:{color};'
        f'border:1px solid {color}55">{value}</span>'
    )


def chip(label: str, value: str, color: str) -> str:
    return (
        f'<span class="dci-chip" style="background:{color}1a;color:{color};'
        f'border:1px solid {color}55">{label}: {value}</span>'
    )


def kpi(col, label: str, value: str, color: str):
    with col.container(border=True):
        st.markdown(
            f'<div class="dci-kpi">'
            f'<div class="dci-kpi-label">{label}</div>'
            f'<div class="dci-kpi-val" style="color:{color}">{value}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Left-column control panel (selection)
# ---------------------------------------------------------------------------
def render_control_panel() -> dict:
    llm = get_llm()
    azure_ok = config.azure_openai_configured() and llm.is_available()
    use_llm = azure_ok
    live_retrieval = config.ENABLE_LIVE_RETRIEVAL
    products = da.list_products()
    cases = da.demo_cases()

    with st.container(border=True):
        st.markdown("#### Analysis controls")
        if azure_ok:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:.4rem;font-weight:600;color:#1f9d55;">'
                '<span style="width:9px;height:9px;border-radius:50%;background:#1f9d55;'
                'box-shadow:0 0 0 3px #1f9d5533;display:inline-block;"></span>'
                'Azure AI service · online</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:.4rem;font-weight:600;color:#7a8493;">'
                '<span style="width:9px;height:9px;border-radius:50%;background:#9aa4b2;'
                'display:inline-block;"></span>'
                'Azure AI service · offline (demo mode)</span>',
                unsafe_allow_html=True,
            )

        st.markdown("**Quick-load scenario**")
        case_labels = ["— none —"] + [
            f"{row['product_a']}  +  {row['product_b']}" for _, row in cases.iterrows()
        ]
        selected = st.selectbox(
            "Preset", case_labels, index=0, label_visibility="collapsed"
        )
        preset = None
        if selected != case_labels[0]:
            idx = case_labels.index(selected) - 1
            preset = cases.iloc[idx].to_dict()

        default_a = preset["product_a"] if preset else "EMROK"
        default_b = preset["product_b"] if preset else "GLIMADAY 2 mg"
        default_q = preset["research_question"] if preset else RESEARCH_QUESTIONS[0]
        idx_a = products.index(default_a) if default_a in products else 0
        idx_b = products.index(default_b) if default_b in products else 1
        q_options = RESEARCH_QUESTIONS.copy()
        if default_q not in q_options:
            q_options = [default_q] + q_options

        st.markdown("**Combination**")
        product_a = st.selectbox("Drug / product A", products, index=idx_a)
        product_b = st.selectbox("Drug / product B", products, index=idx_b)
        research_question = st.selectbox(
            "Research question", q_options, index=q_options.index(default_q)
        )
        st.caption(research_question)
        analyze = st.button("🔬 Analyze combination", type="primary", width="stretch")
        st.caption(
            "Live retrieval: " + ("on" if live_retrieval else "off (cached / offline)")
        )

    return {
        "product_a": product_a,
        "product_b": product_b,
        "research_question": research_question,
        "analyze": analyze,
        "use_llm": use_llm,
        "live_retrieval": live_retrieval,
    }


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def render_header():
    st.markdown(
        f"""
        <div class="dci-hero">
            <div class="dci-eyebrow">Research evidence intelligence · {config.ORG_NAME}</div>
            <h1>🧪 {config.APP_TITLE}</h1>
            <p>{config.APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Research questions (preset framings shown in the control panel)
# ---------------------------------------------------------------------------
RESEARCH_QUESTIONS = [
    "Assess this combination for potential benefit, interaction, toxicity, evidence strength and evidence gaps.",
    "Assess interaction, safety and published combination evidence.",
    "Assess available evidence and identify evidence gaps.",
    "Assess overlapping safety considerations and evidence.",
    "Distinguish established therapy from novel combination evidence.",
]

FOLLOWUP_SUGGESTIONS = [
    "Which evidence gap should we prioritise closing first, and why?",
    "What is the strongest piece of evidence behind this assessment?",
    "Are there contradictions between the sources?",
    "What additional sources would raise our confidence?",
    "Summarise the key toxicity considerations for a researcher.",
]


# ---------------------------------------------------------------------------
# Workflow runner — compact, collapses when done
# ---------------------------------------------------------------------------
def run_and_render_progress(sel: dict, cfg: dict) -> AnalysisResult:
    result_holder = {}
    with st.status("Running agent workflow…", expanded=True) as status:
        for item in orchestrator.run_pipeline(
            product_a=sel["product_a"],
            product_b=sel["product_b"],
            research_question=sel["research_question"],
            use_llm=cfg["use_llm"],
            live_retrieval=cfg["live_retrieval"],
        ):
            if isinstance(item, AnalysisResult):
                result_holder["result"] = item
            else:
                label, state = item
                if state == "done":
                    st.write(f"✅ {label}")
        status.update(label="Agent workflow complete", state="complete", expanded=False)
    return result_holder["result"]


# ---------------------------------------------------------------------------
# Result rendering
# ---------------------------------------------------------------------------
def _signal_box(col, title: str, level: str, lines: list, caption: str = "", extra: str = ""):
    color = SIGNAL_COLORS.get(level, "#6c5ce7")
    with col.container(border=True, height="stretch"):
        st.markdown(
            f"<div class='dci-kpi-label'>{title}</div>{pill(level, color)}",
            unsafe_allow_html=True,
        )
        if extra:
            st.caption(extra)
        for ln in lines[:3]:
            st.markdown(f"- {ln}")
        if caption:
            st.caption(caption)


def render_assessment(result: AnalysisResult):
    a = result.assessment
    color = ASSESSMENT_COLORS.get(a.overall_assessment, "#5b6675")
    mode_tag = "AI synthesis (Azure)" if result.mode == "azure" else "Deterministic demo"
    live_tag = " · live retrieval" if result.live_retrieval_used else ""

    with st.container(border=True):
        st.markdown(
            f'<div class="dci-drugs">{a.drug_a} &nbsp;+&nbsp; {a.drug_b}</div>'
            f'<span class="dci-prov">Mode: {mode_tag}{live_tag}</span>'
            f'<div style="margin-top:.6rem">{badge(a.overall_assessment, color)}</div>',
            unsafe_allow_html=True,
        )
        st.write("")

        r1 = st.columns(2)
        kpi(r1[0], "Overall assessment", a.overall_assessment, color)
        kpi(r1[1], "AI confidence", f"{a.confidence}%", "#12a4a4")
        r2 = st.columns(2)
        kpi(r2[0], "Evidence strength", a.evidence_strength, "#0f6cbd")
        kpi(r2[1], "Interaction signal", a.interaction_signal, SIGNAL_COLORS.get(a.interaction_signal, "#6c5ce7"))
        r3 = st.columns(2)
        kpi(r3[0], "Toxicity signal", a.toxicity_signal, SIGNAL_COLORS.get(a.toxicity_signal, "#6c5ce7"))
        kpi(r3[1], "Benefit signal", a.benefit_signal, SIGNAL_COLORS.get(a.benefit_signal, "#6c5ce7"))

        if a.why_bullets:
            st.markdown("**Reasoning**")
            for b in a.why_bullets[:4]:
                st.markdown(f"- {b}")


def _signals_tab(result: AnalysisResult):
    ia, tox = result.interaction, result.toxicity
    c1, c2 = st.columns(2)
    with c1.container(border=True):
        st.markdown(
            f"<div class='dci-kpi-label'>Interaction signal</div>"
            f"{pill(ia.interaction_signal, SIGNAL_COLORS.get(ia.interaction_signal, '#6c5ce7'))}",
            unsafe_allow_html=True,
        )
        st.caption(f"Class: {ia.interaction_class}")
        if ia.mechanism_summary:
            st.caption(ia.mechanism_summary)
        for f in ia.findings[:4]:
            st.markdown(f"- {f}")
        st.caption(ia.caveat)
    with c2.container(border=True):
        st.markdown(
            f"<div class='dci-kpi-label'>Toxicity signal</div>"
            f"{pill(tox.toxicity_signal, SIGNAL_COLORS.get(tox.toxicity_signal, '#6c5ce7'))}",
            unsafe_allow_html=True,
        )
        if tox.organ_specific_concerns:
            st.caption("Organs: " + ", ".join(tox.organ_specific_concerns))
        for f in tox.findings[:4]:
            st.markdown(f"- {f}")
        st.caption(tox.causality_caveat)


def _evidence_tab(result: AnalysisResult):
    counts = result.evidence_counts()
    c = st.columns(4)
    c[0].metric("Internal research", counts["internal"])
    c[1].metric("Regulatory / label", counts["regulatory"])
    c[2].metric("Published literature", counts["literature"])
    c[3].metric("Combination evidence", counts["combination"])
    st.caption("Counts reflect actually-retrieved / synthetic evidence only — planned queries excluded.")
    planned = sum(1 for e in result.evidence if e.provenance_status == "planned_not_retrieved")
    if planned:
        st.caption(f"➕ {planned} additional public source quer{'y' if planned == 1 else 'ies'} were planned (not executed) — see Citations.")
    if any(e.provenance_status == "synthetic" for e in result.evidence):
        st.markdown(
            '<span class="dci-chip" style="background:#6c5ce71a;color:#6c5ce7;'
            'border:1px solid #6c5ce755">Synthetic demonstration data present</span>',
            unsafe_allow_html=True,
        )


def _synthesis_tab(result: AnalysisResult):
    s = result.synthesis
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Supporting evidence**")
        if s.supporting_evidence:
            for e in s.supporting_evidence:
                st.markdown(f"- {e}")
        else:
            st.caption("None retrieved.")
        st.markdown("**Contradictory evidence**")
        if s.contradictory_evidence:
            for e in s.contradictory_evidence:
                st.markdown(f"- {e}")
        else:
            st.caption("None identified.")
    with c2:
        st.markdown("**Evidence gaps**")
        for g in s.evidence_gaps:
            st.markdown(f"- {g}")
        if s.source_quality_notes:
            st.markdown("**Source quality**")
            for n in s.source_quality_notes:
                st.caption(n)


def _citation_card(e):
    color = prov_color(e.provenance_status)
    with st.container(border=True):
        cols = st.columns([3.2, 1], vertical_alignment="center")
        with cols[0]:
            title = e.source_name
            if e.source_identifier:
                title += f"  ·  {e.source_identifier}"
            st.markdown(f"**{title}**")
            st.caption(f"{e.evidence_layer} · {e.authority_level}")
        with cols[1]:
            link = (
                f" &nbsp; <a href='{e.source_url}' target='_blank'>open ↗</a>"
                if e.source_url
                else ""
            )
            st.markdown(
                f"<div style='text-align:right'>{pill(e.provenance_status, color)}{link}</div>",
                unsafe_allow_html=True,
            )
        if e.evidence_excerpt_or_summary:
            st.caption(e.evidence_excerpt_or_summary)


def _citations_tab(result: AnalysisResult):
    st.caption(
        "Provenance: synthetic = demonstration · cached / retrieved = real public source · "
        "planned_not_retrieved = query plan only."
    )
    with st.container(height=430):
        for e in result.evidence:
            _citation_card(e)


def _json_tab(result: AnalysisResult):
    st.markdown("**Structured assessment (Pydantic output)**")
    st.json(result.assessment.model_dump())
    with st.expander("Interaction · Toxicity · Synthesis (JSON)"):
        st.json(
            {
                "interaction": result.interaction.model_dump(),
                "toxicity": result.toxicity.model_dump(),
                "synthesis": result.synthesis.model_dump(),
            }
        )
    with st.expander("Evidence items (JSON)"):
        st.json([e.model_dump() for e in result.evidence])


def render_result_tabs(result: AnalysisResult):
    with st.container(border=True):
        t0, t1, t2, t3, t4 = st.tabs(
            ["Signals", "Evidence", "Synthesis & gaps", "Citations", "JSON output"]
        )
        with t0:
            _signals_tab(result)
        with t1:
            _evidence_tab(result)
        with t2:
            _synthesis_tab(result)
        with t3:
            _citations_tab(result)
        with t4:
            _json_tab(result)


def render_human_review():
    st.markdown(
        '<div class="dci-review">🧑‍🔬 <b>Human review required.</b> A researcher must '
        "review before any scientific or clinical decision. This tool synthesizes and "
        "traces evidence; it does not make clinical recommendations.</div>",
        unsafe_allow_html=True,
    )


def _followup_payload(result: AnalysisResult, question: str) -> dict:
    a = result.assessment
    return {
        "question": question,
        "assessment": {
            "drug_a": a.drug_a,
            "drug_b": a.drug_b,
            "overall_assessment": a.overall_assessment,
            "benefit_signal": a.benefit_signal,
            "interaction_signal": a.interaction_signal,
            "toxicity_signal": a.toxicity_signal,
            "evidence_strength": a.evidence_strength,
            "evidence_gaps": a.evidence_gaps,
            "why_bullets": a.why_bullets,
        },
        "evidence": [
            {
                "source_name": e.source_name,
                "source_identifier": e.source_identifier,
                "authority_level": e.authority_level,
                "provenance_status": e.provenance_status,
                "summary": e.evidence_excerpt_or_summary,
            }
            for e in result.evidence
        ],
    }


def answer_followup(result: AnalysisResult, question: str) -> dict:
    """Ask the Azure model a grounded follow-up. Raises LLMUnavailable on failure."""
    llm = get_llm()
    data = llm.complete_json(
        load_prompt("followup"),
        json.dumps(_followup_payload(result, question), ensure_ascii=False),
    )
    return data


@st.fragment
def render_followup(result: AnalysisResult):
    llm = get_llm()
    azure_ok = llm.is_available()

    with st.container(border=True):
        st.markdown("#### Ask a follow-up")
        choice = st.selectbox(
            "Suggested questions",
            ["— select a sample question —"] + FOLLOWUP_SUGGESTIONS,
            index=0,
            key="fu_choice",
        )
        custom = st.text_input(
            "Or type your own",
            placeholder="e.g. How recent is the supporting literature?",
            key="fu_custom",
        )
        ask = st.button("Ask", type="primary", key="fu_ask")

        question = custom.strip() if custom.strip() else (
            "" if choice.startswith("—") else choice
        )

        if ask:
            if not question:
                st.session_state.pop("fu_answer", None)
                st.caption("Please select or type a question first.")
            elif azure_ok:
                try:
                    with st.spinner("Synthesizing a grounded answer from the traced evidence…"):
                        data = answer_followup(result, question)
                    st.session_state["fu_answer"] = {
                        "q": question,
                        "answer": str(data.get("answer", "")).strip(),
                        "used": data.get("used_sources", []) or [],
                        "caveat": str(data.get("caveat", "")).strip(),
                    }
                except LLMUnavailable as exc:
                    st.session_state["fu_answer"] = {"q": question, "error": str(exc)}
            else:
                st.session_state["fu_answer"] = {"q": question, "offline": True}

        # Persisted answer — survives reruns so it never flickers away.
        ans = st.session_state.get("fu_answer")
        if ans:
            with st.chat_message("assistant"):
                st.markdown(f"**Q:** {ans['q']}")
                if ans.get("error"):
                    st.warning("Azure synthesis was unavailable. (" + ans["error"] + ")")
                elif ans.get("offline"):
                    st.info("Offline demo mode — the answer is the traced evidence above.")
                else:
                    st.markdown(ans.get("answer") or "_No answer produced._")
                    if ans.get("used"):
                        st.markdown("**Sources used:** " + " · ".join(f"`{s}`" for s in ans["used"]))
                    st.caption(
                        (ans.get("caveat") or "Grounded in the traced evidence above.")
                        + " Researcher review required; not a clinical recommendation."
                    )
        elif not ask:
            st.caption(
                "Pick a sample question or type your own, then click Ask."
                if azure_ok
                else "Offline demo mode — configure Azure OpenAI for grounded free-form answers."
            )


def render_empty_state():
    with st.container(border=True):
        st.markdown("#### Results")
        st.caption(
            "Select a combination on the left and click **Analyze combination**. "
            "The traceable assessment, signals, evidence, citations and JSON output "
            "will appear here."
        )
        st.markdown(
            "The agent workflow runs: normalize → search internal → search public "
            "→ analyze interaction → analyze toxicity → synthesize → assess."
        )


def main():
    render_header()

    left, right = st.columns([1.35, 2], gap="large")

    with left:
        ctrl = render_control_panel()

    with right:
        if ctrl["analyze"]:
            if ctrl["product_a"] == ctrl["product_b"]:
                st.warning("Please select two different products.")
            else:
                result = run_and_render_progress(ctrl, ctrl)
                st.session_state["last_result"] = result
                st.session_state.pop("fu_answer", None)

        result = st.session_state.get("last_result")
        if result is not None:
            render_assessment(result)
            render_result_tabs(result)
            render_human_review()
            render_followup(result)
        else:
            render_empty_state()


if __name__ == "__main__":
    main()
