"""Structured data access over the supplied CSV package.

All reads are cached in-process. Column names match the supplied schemas
exactly; nothing is fabricated here.
"""
from __future__ import annotations

import functools
import os
from typing import List, Optional

import pandas as pd

import config


@functools.lru_cache(maxsize=None)
def _read_csv_cached(path_str: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path_str, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    return df


def _read_csv(path_str: str) -> pd.DataFrame:
    # Include the file's modified time in the cache key so edits are picked up
    # automatically (no server restart needed).
    try:
        mtime = os.path.getmtime(path_str)
    except OSError:
        mtime = 0.0
    return _read_csv_cached(path_str, mtime)


def drug_master() -> pd.DataFrame:
    return _read_csv(str(config.DRUG_MASTER))


def ingredient_master() -> pd.DataFrame:
    return _read_csv(str(config.INGREDIENT_MASTER))


def internal_research() -> pd.DataFrame:
    return _read_csv(str(config.INTERNAL_COMBINATION_RESEARCH))


def demo_cases() -> pd.DataFrame:
    return _read_csv(str(config.DEMO_CASE_LIBRARY))


def source_registry() -> pd.DataFrame:
    return _read_csv(str(config.PUBLIC_SOURCE_REGISTRY))


def evidence_recipes() -> pd.DataFrame:
    return _read_csv(str(config.PUBLIC_EVIDENCE_RECIPES))


def source_manifest() -> pd.DataFrame:
    return _read_csv(str(config.SOURCE_MANIFEST))


# ---------------------------------------------------------------------------
# Product / ingredient lookups
# ---------------------------------------------------------------------------
def list_products() -> List[str]:
    df = drug_master()
    return sorted(df["product_name"].unique().tolist())


def get_product_row(product_name: str) -> Optional[dict]:
    df = drug_master()
    match = df[df["product_name"].str.casefold() == product_name.casefold()]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def split_ingredients(active_ingredient_text: str) -> List[str]:
    """Split the semicolon-delimited ingredient text into components."""
    if not active_ingredient_text:
        return []
    parts = [p.strip() for p in active_ingredient_text.split(";")]
    return [p for p in parts if p]


def find_ingredient_row(ingredient_name: str) -> Optional[dict]:
    df = ingredient_master()
    name = ingredient_name.strip().casefold()
    # exact match on ingredient_name or normalized_name
    for col in ("ingredient_name", "normalized_name"):
        match = df[df[col].str.casefold() == name]
        if not match.empty:
            return match.iloc[0].to_dict()
    return None


def normalized_ingredient(ingredient_name: str) -> str:
    row = find_ingredient_row(ingredient_name)
    if row:
        return row.get("normalized_name") or row.get("ingredient_name") or ingredient_name
    return ingredient_name


def all_normalized_ingredients_for_product(product_name: str) -> List[str]:
    row = get_product_row(product_name)
    if not row:
        return []
    names = split_ingredients(row.get("active_ingredient_text", ""))
    return [normalized_ingredient(n) for n in names]
