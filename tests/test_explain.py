"""
tests/test_explain.py — Unit tests for the human-readable explanation generator.
"""

import json
from pathlib import Path
from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.pipeline import evaluate_candidate
from meritengine.core.explain import generate_explanation

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_candidate(filename: str) -> Candidate:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(filename: str) -> RoleSpec:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def test_explanation_polished():
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    verdict = evaluate_candidate(polished, role)
    verdict = generate_explanation(verdict, polished)

    assert "Arjun Mehta" in verdict.human_review_notes
    assert "Dimension Breakdown" in verdict.human_review_notes
    assert "Pedigree Dampening Applied" in verdict.human_review_notes
    assert "Google" in verdict.human_review_notes
    assert "Risk Factors" in verdict.human_review_notes or "Red Flags" in verdict.human_review_notes


def test_explanation_promising():
    promising = load_candidate("candidate_promising.json")
    role = load_role("role_backend_senior.json")

    verdict = evaluate_candidate(promising, role)
    verdict = generate_explanation(verdict, promising)

    assert "Priya Sharma" in verdict.human_review_notes
    assert "Growth Boost Applied" in verdict.human_review_notes
    assert "No Red Flags" in verdict.human_review_notes
