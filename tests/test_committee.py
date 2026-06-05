"""
tests/test_committee.py — Unit tests for the empathy-first judging committee.
"""

import json
from pathlib import Path
from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.scoring.committee import CommitteeEvaluator
from meritengine.core.pipeline import evaluate_candidate

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_candidate(filename: str) -> Candidate:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(filename: str) -> RoleSpec:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def test_committee_evaluator_direct():
    candidate = load_candidate("candidate_promising.json")
    role = load_role("role_backend_senior.json")

    committee = CommitteeEvaluator()
    result = committee.evaluate(candidate, role)

    # Verify we ran all 50 agents
    assert len(result["logs"]) == 50
    assert result["score_boost"] > 0
    assert len(result["advocacy_notes"]) > 0

    # Ensure advocacy notes contain detailed signals
    advocacy_text = "".join(result["advocacy_notes"])
    assert "Self-Made Builder Sponsor" in advocacy_text or "Commit Cadence" in advocacy_text


def test_pipeline_integration_with_committee():
    candidate = load_candidate("candidate_promising.json")
    role = load_role("role_backend_senior.json")

    verdict = evaluate_candidate(candidate, role)

    # Check that human review notes were populated by the committee
    assert "=== EMPATHETIC COMMITTEE ADVOCACY NARRATIVE ===" in verdict.human_review_notes
    assert "Ombudsman Verdict" in verdict.human_review_notes
    assert len(verdict.human_review_notes) > 100
