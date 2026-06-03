"""
tests/test_aggregate.py — Unit tests for the score aggregator.
"""

import json
from pathlib import Path
from meritengine.core.models import Candidate, RoleSpec, Dimensions, DimensionScore
from meritengine.core.scoring.aggregate import aggregate_scores

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_candidate(filename: str) -> Candidate:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(filename: str) -> RoleSpec:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def _dim(score: int) -> DimensionScore:
    return DimensionScore(score=score, evidence=["Test evidence"], rationale="Test rationale")


def test_aggregation_promising_outranks_polished():
    role = load_role("role_backend_senior.json")
    
    # Candidate A: Polished (Arjun Mehta)
    polished = load_candidate("candidate_polished.json")
    # Suppose Arjun gets good base scores in Job Fit and Reliability because of experience,
    # but low in demonstrated skill/hunger/creativity.
    polished_dims = Dimensions(
        skill=_dim(20),       # No public github / code
        hunger=_dim(15),      # No activity signals, slow response
        creativity=_dim(10),  # No side projects, no assessment
        job_fit=_dim(85),     # Matches senior role years/title
        reliability=_dim(80), # Standard brand-based credentials
    )

    # Candidate B: Promising (Priya Sharma)
    promising = load_candidate("candidate_promising.json")
    # Priya has excellent demonstrated work.
    promising_dims = Dimensions(
        skill=_dim(90),       # High assessment + repos
        hunger=_dim(95),      # Extremely high commits and streak
        creativity=_dim(85),  # Unconventional event-sourcing solution
        job_fit=_dim(75),     # Startup experience, matches tech stack
        reliability=_dim(90), # High response and follow-through rates
    )

    verdict_polished = aggregate_scores(polished, role, polished_dims)
    verdict_promising = aggregate_scores(promising, role, promising_dims)

    # Verify pedigree dampening was applied to polished candidate
    assert verdict_polished.pedigree_adjustment.applied is True
    # Verify growth boost was applied to promising candidate
    assert verdict_promising.growth_signal.detected is True
    assert verdict_promising.growth_signal.multiplier_applied == 1.15

    # Critical requirement: Promising candidate outranks Polished candidate
    assert verdict_promising.overall > verdict_polished.overall
    
    # Promising should be a hire/strong_hire, Polished should be hold/pass
    assert verdict_promising.verdict in ("hire", "strong_hire")
    assert verdict_polished.verdict in ("hold", "pass")
    
    # Candidate type categorization
    assert verdict_promising.candidate_type == "promising"
    assert verdict_polished.candidate_type == "polished"
