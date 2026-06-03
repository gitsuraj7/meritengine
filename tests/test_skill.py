"""
tests/test_skill.py — Unit tests for the skill scoring engine.
"""

import json
from pathlib import Path
from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.scoring.skill import evaluate_skill

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_candidate(filename: str) -> Candidate:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(filename: str) -> RoleSpec:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def test_evaluate_skill_promising_candidate():
    candidate = load_candidate("candidate_promising.json")
    role = load_role("role_backend_senior.json")

    result = evaluate_skill(candidate, role)

    # Priya has strong assessment, repos, and side projects.
    assert result.score >= 80
    assert len(result.evidence) > 0
    assert "GitHub profile" in "".join(result.evidence)
    assert "Assessment solution is verified as working" in "".join(result.evidence)
    assert "Exceptional demonstrated technical capability" in result.rationale


def test_evaluate_skill_polished_candidate():
    candidate = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    result = evaluate_skill(candidate, role)

    # Arjun has no demonstrated artifacts.
    assert result.score < 20
    assert "No technical coding assessment" in "".join(result.evidence)
    assert "No public GitHub profile" in "".join(result.evidence)
    assert "Low verifiable technical capability" in result.rationale


def test_evaluate_skill_minimal_candidate():
    candidate = Candidate(id="min-001", name="Minimal Candidate")
    role = load_role("role_backend_senior.json")

    result = evaluate_skill(candidate, role)

    assert result.score == 0
    assert "No technical coding assessment" in "".join(result.evidence)
    assert "No public GitHub profile" in "".join(result.evidence)
    assert "Low verifiable technical capability" in result.rationale
