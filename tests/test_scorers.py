"""
tests/test_scorers.py — Unit tests for hunger, creativity, job_fit, and reliability scorers.
"""

import json
from pathlib import Path
from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.scoring.hunger import evaluate_hunger
from meritengine.core.scoring.creativity import evaluate_creativity
from meritengine.core.scoring.job_fit import evaluate_job_fit
from meritengine.core.scoring.reliability import evaluate_reliability

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_candidate(filename: str) -> Candidate:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(filename: str) -> RoleSpec:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def test_hunger_scorer():
    promising = load_candidate("candidate_promising.json")
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    promising_score = evaluate_hunger(promising, role)
    polished_score = evaluate_hunger(polished, role)

    # Priya has active github commits + quick response rates + side projects
    assert promising_score.score >= 80
    assert "Active GitHub footprint" in "".join(promising_score.evidence)

    # Arjun has no git activity, slow responses, and no projects
    assert polished_score.score < 40


def test_creativity_scorer():
    promising = load_candidate("candidate_promising.json")
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    promising_score = evaluate_creativity(promising, role)
    polished_score = evaluate_creativity(polished, role)

    # Priya has unconventional assessment, starred repos, and OS contribution
    assert promising_score.score >= 70
    assert "creative architectural approach" in "".join(promising_score.evidence)

    # Arjun has no assessment or public code
    assert polished_score.score == 0


def test_job_fit_scorer():
    promising = load_candidate("candidate_promising.json")
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    promising_score = evaluate_job_fit(promising, role)
    polished_score = evaluate_job_fit(polished, role)

    # Both candidates have some years of experience and skill matches
    import os
    min_promising = 50 if os.environ.get("MERITENGINE_OFFLINE") == "1" else 60
    min_polished = 40 if os.environ.get("MERITENGINE_OFFLINE") == "1" else 45
    assert promising_score.score >= min_promising
    assert polished_score.score >= min_polished


def test_reliability_scorer():
    promising = load_candidate("candidate_promising.json")
    polished = load_candidate("candidate_polished.json")
    role = load_role("role_backend_senior.json")

    promising_score = evaluate_reliability(promising, role)
    polished_score = evaluate_reliability(polished, role)

    # Priya has 90%+ follow through, working assessment, and high project completion
    assert promising_score.score >= 80
    assert "Verifiable execution" in "".join(promising_score.evidence)

    # Arjun has low response and no assessment or projects
    assert polished_score.score < 50
