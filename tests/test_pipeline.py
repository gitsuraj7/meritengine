"""
tests/test_pipeline.py — Unit and integration tests for the orchestration pipeline.
"""

import json
from pathlib import Path
from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.pipeline import evaluate_candidate, rank_candidates

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_candidate(filename: str) -> Candidate:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(filename: str) -> RoleSpec:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def test_end_to_end_evaluation():
    promising = load_candidate("candidate_promising.json")
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    verdict_promising = evaluate_candidate(promising, role)
    verdict_polished = evaluate_candidate(polished, role)

    # Priya has rich GitHub presence, a working assessment, and side projects
    assert verdict_promising.dimensions.skill.score >= 80
    assert verdict_promising.growth_signal.detected is True
    assert verdict_promising.verdict in ("hire", "strong_hire")

    # Arjun has no demonstrated artifacts
    assert verdict_polished.dimensions.skill.score < 20
    assert verdict_polished.pedigree_adjustment.applied is True
    assert verdict_polished.verdict in ("hold", "pass")


def test_ranking_pipeline():
    promising = load_candidate("candidate_promising.json")
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    result = rank_candidates([polished, promising], role)

    assert result.total_evaluated == 2
    assert result.total_passed >= 1
    
    # Promising candidate (Priya) MUST be ranked #1
    assert result.candidates[0].verdict.candidate_id == "promising-001"
    assert result.candidates[0].rank == 1
    
    # Polished candidate (Arjun) MUST be ranked #2
    assert result.candidates[1].verdict.candidate_id == "polished-001"
    assert result.candidates[1].rank == 2
