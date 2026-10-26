# Drug Combination Intelligence — Starter Data Package

Created: 2026-08-18

## Purpose
Starter knowledge/data package for an AI-assisted Drug Combination Intelligence application.

## Important provenance rules
- `company/` contains product facts extracted from the public Acme Pharma Branded Products page.
- `internal/` combination research records are explicitly SYNTHETIC demonstration data. They must never be presented as real internal research or clinical evidence.
- `public/` contains the authoritative source registry and repeatable collection recipes. It intentionally avoids fabricating public findings where the current session did not retrieve the underlying record.
- Every public evidence record added later must retain source URL/identifier, retrieval date, source type, and a short provenance note.
- This application is a research-information demonstrator, not a clinical decision-support system and must not make treatment recommendations.

## Recommended next collection step
Run a controlled enrichment pipeline for the normalized ingredients using RxNorm, PubChem, PubMed/NCBI, DailyMed, openFDA and a licensed/authorized combination dataset where permitted. Store source identifiers and citations rather than copying copyrighted full text.

## Product source
https://example.com/products
