"""Shared agent context and helpers."""
from __future__ import annotations

import functools
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import config
from models.schemas import (
    CombinationAssessment,
    DrugIdentity,
    EvidenceItem,
    EvidenceSynthesis,
    InteractionAnalysis,
    ToxicityAnalysis,
)
from services.demo_knowledge import PairReasoning

PROMPTS_DIR = config.PROJECT_ROOT / "prompts"


@functools.lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


@dataclass
class AgentContext:
    """Mutable context threaded through the agent pipeline."""

    product_a: str
    product_b: str
    research_question: str = ""
    use_llm: bool = False
    live_retrieval: bool = False

    identity_a: Optional[DrugIdentity] = None
    identity_b: Optional[DrugIdentity] = None
    ingredients_a: List[str] = field(default_factory=list)
    ingredients_b: List[str] = field(default_factory=list)

    evidence: List[EvidenceItem] = field(default_factory=list)
    reasoning: Optional[PairReasoning] = None

    interaction: Optional[InteractionAnalysis] = None
    toxicity: Optional[ToxicityAnalysis] = None
    synthesis: Optional[EvidenceSynthesis] = None
    assessment: Optional[CombinationAssessment] = None

    # One-shot combined LLM reasoning (populated once, reused by all 4 agents).
    combined_llm: Optional[dict] = None
    combined_llm_attempted: bool = False

    def primary_ingredient_a(self) -> str:
        return self.ingredients_a[0] if self.ingredients_a else self.product_a

    def primary_ingredient_b(self) -> str:
        return self.ingredients_b[0] if self.ingredients_b else self.product_b
