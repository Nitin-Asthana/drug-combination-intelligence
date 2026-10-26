"""Offline validation harness.

Runs the full agent pipeline in deterministic demo mode across every demo case
and a same-drug guard case, printing each Combination Assessment. Also asserts
the safety guardrails hold (no forbidden terms; human review always required).

Usage:  python -m validate
"""
from __future__ import annotations

import sys

from agents import orchestrator
from models.schemas import FORBIDDEN_ASSESSMENT_TERMS, OVERALL_ASSESSMENTS
from services import data_access as da


def _check(result) -> list:
    problems = []
    a = result.assessment
    if a.overall_assessment not in OVERALL_ASSESSMENTS:
        problems.append(f"Invalid assessment label: {a.overall_assessment}")
    if not a.human_review_required:
        problems.append("human_review_required must be True")
    for term in FORBIDDEN_ASSESSMENT_TERMS:
        blob = (a.rationale + " " + " ".join(a.why_bullets)).lower()
        if term in blob.split():
            problems.append(f"Forbidden term '{term}' present in output")
    if not (0 <= a.confidence <= 100):
        problems.append(f"Confidence out of range: {a.confidence}")
    return problems


def main() -> int:
    cases = da.demo_cases()
    total_problems = 0

    for _, row in cases.iterrows():
        result = orchestrator.analyze(
            product_a=row["product_a"],
            product_b=row["product_b"],
            research_question=row["research_question"],
            use_llm=False,
            live_retrieval=False,
        )
        a = result.assessment
        counts = result.evidence_counts()
        print("=" * 78)
        print(f"{row['case_id']}: {a.drug_a}  +  {a.drug_b}")
        print(f"  Assessment : {a.overall_assessment}")
        print(f"  Signals    : benefit={a.benefit_signal} interaction={a.interaction_signal} toxicity={a.toxicity_signal}")
        print(f"  Strength   : {a.evidence_strength}  Confidence: {a.confidence}%")
        print(f"  Evidence   : internal={counts['internal']} regulatory={counts['regulatory']} literature={counts['literature']} combination={counts['combination']}")
        problems = _check(result)
        total_problems += len(problems)
        for p in problems:
            print(f"  !! GUARDRAIL: {p}")

    print("=" * 78)
    if total_problems == 0:
        print("All demo cases passed guardrail checks.")
        return 0
    print(f"{total_problems} guardrail problem(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
