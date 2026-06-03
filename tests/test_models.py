"""
tests/test_models.py — Model validation tests for MeritEngine.

Tests three things:
  1. Valid fixture data passes Pydantic validation and fields parse correctly.
  2. Invalid data (out-of-range scores, bad enums) raises ValidationError.
  3. The output contract (CandidateVerdict) serializes to the exact JSON shape
     defined in Section 3 of the build directive.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from meritengine.core.models import (
    Assessment,
    BehavioralSignals,
    Candidate,
    CandidateVerdict,
    DimensionScore,
    Dimensions,
    Education,
    GitHubProfile,
    GitHubRepo,
    GrowthSignal,
    PedigreeAdjustment,
    RankedCandidate,
    RankingResult,
    RoleSpec,
    SideProject,
    SkillRequirement,
    WorkExperience,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════════
# Candidate input model
# ═══════════════════════════════════════════════════════════════════════════════


class TestCandidateModel:
    def test_polished_candidate_loads(self):
        data = load_fixture("candidate_polished.json")
        c = Candidate(**data)
        assert c.id == "polished-001"
        assert c.name == "Arjun Mehta"
        assert len(c.education) == 1
        assert c.education[0].is_tier1 is True
        assert c.education[0].institution == "IIT Bombay"
        assert len(c.work_experience) == 2
        assert c.work_experience[0].is_faang_or_brand is True
        assert c.work_experience[0].company == "Google"
        assert c.github is None
        assert c.assessment is None
        assert len(c.side_projects) == 0

    def test_promising_candidate_loads(self):
        data = load_fixture("candidate_promising.json")
        c = Candidate(**data)
        assert c.id == "promising-001"
        assert c.name == "Priya Sharma"
        assert c.education[0].is_tier1 is False
        # GitHub present with real data
        assert c.github is not None
        assert c.github.total_repos == 12
        assert c.github.total_commits_last_year == 847
        assert c.github.contribution_streak_days == 94
        assert len(c.github.repos) == 3
        # Production repos
        prod_repos = [r for r in c.github.repos if r.is_production]
        assert len(prod_repos) == 2
        # Assessment submitted and unconventional
        assert c.assessment is not None
        assert c.assessment.submitted is True
        assert c.assessment.is_unconventional is True
        assert c.assessment.is_working is True
        assert c.assessment.score == 88
        # Side projects
        assert len(c.side_projects) == 3
        completed = [p for p in c.side_projects if p.status == "completed"]
        assert len(completed) == 2

    def test_minimal_candidate_valid(self):
        """A candidate with only id and name should still be valid."""
        c = Candidate(id="min-001", name="Minimal")
        assert c.id == "min-001"
        assert c.skills_claimed == []
        assert c.education == []
        assert c.work_experience == []
        assert c.github is None
        assert c.assessment is None
        assert c.behavioral is None
        assert c.total_experience_months == 0

    def test_whitespace_stripped(self):
        c = Candidate(id="  ws-001  ", name="  Whitespace Test  ")
        assert c.id == "ws-001"
        assert c.name == "Whitespace Test"

    def test_negative_experience_months_rejected(self):
        with pytest.raises(ValidationError):
            Candidate(id="bad-001", name="Bad", total_experience_months=-5)

    def test_negative_ctc_rejected(self):
        with pytest.raises(ValidationError):
            Candidate(id="bad-002", name="Bad", current_ctc=-100000)


# ═══════════════════════════════════════════════════════════════════════════════
# RoleSpec input model
# ═══════════════════════════════════════════════════════════════════════════════


class TestRoleSpecModel:
    def test_role_fixture_loads(self):
        data = load_fixture("role_backend_senior.json")
        r = RoleSpec(**data)
        assert r.title == "Senior Backend Engineer"
        assert r.seniority == "senior"
        assert r.environment == "startup"
        assert r.domain == "fintech"
        assert r.remote_ok is True
        assert r.budget_max_ctc == 3_500_000
        # Skill counts
        must_haves = [s for s in r.required_skills if s.priority == "must_have"]
        nice_to_haves = [s for s in r.required_skills if s.priority == "nice_to_have"]
        assert len(must_haves) == 4
        assert len(nice_to_haves) == 3
        # Culture signals parsed
        assert "ownership" in r.culture_signals
        assert "fast-paced" in r.culture_signals

    def test_invalid_seniority_rejected(self):
        with pytest.raises(ValidationError):
            RoleSpec(title="Test", seniority="god-tier")

    def test_invalid_environment_rejected(self):
        with pytest.raises(ValidationError):
            RoleSpec(title="Test", environment="metaverse")

    def test_invalid_skill_priority_rejected(self):
        with pytest.raises(ValidationError):
            SkillRequirement(name="Python", priority="mandatory")

    def test_negative_experience_bounds_rejected(self):
        with pytest.raises(ValidationError):
            RoleSpec(title="Test", min_experience_months=-12)


# ═══════════════════════════════════════════════════════════════════════════════
# Sub-models — targeted validation checks
# ═══════════════════════════════════════════════════════════════════════════════


class TestSubModels:
    def test_work_experience_negative_duration_rejected(self):
        with pytest.raises(ValidationError):
            WorkExperience(company="X", title="Y", duration_months=-1)

    def test_github_repo_negative_stars_rejected(self):
        with pytest.raises(ValidationError):
            GitHubRepo(name="bad", stars=-10)

    def test_assessment_score_over_100_rejected(self):
        with pytest.raises(ValidationError):
            Assessment(submitted=True, score=150)

    def test_assessment_score_below_0_rejected(self):
        with pytest.raises(ValidationError):
            Assessment(submitted=True, score=-1)

    def test_behavioral_response_rate_over_1_rejected(self):
        with pytest.raises(ValidationError):
            BehavioralSignals(response_rate=1.5)

    def test_behavioral_clarity_below_0_rejected(self):
        with pytest.raises(ValidationError):
            BehavioralSignals(communication_clarity=-0.1)

    def test_side_project_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            SideProject(name="X", status="maybe")


# ═══════════════════════════════════════════════════════════════════════════════
# DimensionScore
# ═══════════════════════════════════════════════════════════════════════════════


class TestDimensionScore:
    def test_valid_score(self):
        d = DimensionScore(
            score=75,
            evidence=["shipped 3 production projects"],
            rationale="Strong shipping record with real deployment evidence.",
        )
        assert d.score == 75
        assert len(d.evidence) == 1

    def test_score_0_valid(self):
        d = DimensionScore(score=0, evidence=[], rationale="No evidence found.")
        assert d.score == 0

    def test_score_100_valid(self):
        d = DimensionScore(score=100, evidence=["perfect"], rationale="Exceptional.")
        assert d.score == 100

    def test_score_101_rejected(self):
        with pytest.raises(ValidationError):
            DimensionScore(score=101, evidence=[], rationale="")

    def test_score_negative_rejected(self):
        with pytest.raises(ValidationError):
            DimensionScore(score=-1, evidence=[], rationale="")


# ═══════════════════════════════════════════════════════════════════════════════
# PedigreeAdjustment and GrowthSignal
# ═══════════════════════════════════════════════════════════════════════════════


class TestPedigreeAdjustment:
    def test_defaults(self):
        p = PedigreeAdjustment()
        assert p.applied is False
        assert p.discount_factor == 0.3
        assert p.net_score_change == 0.0
        assert p.signals_found == []

    def test_discount_factor_over_1_rejected(self):
        with pytest.raises(ValidationError):
            PedigreeAdjustment(discount_factor=1.5)

    def test_discount_factor_negative_rejected(self):
        with pytest.raises(ValidationError):
            PedigreeAdjustment(discount_factor=-0.1)

    def test_full_adjustment_valid(self):
        p = PedigreeAdjustment(
            applied=True,
            signals_found=["IIT Bombay", "Google internship"],
            discount_factor=0.3,
            net_score_change=-8.5,
            reason="pedigree signals discounted per anti-bias policy",
        )
        assert p.applied is True
        assert len(p.signals_found) == 2
        assert p.net_score_change == -8.5


class TestGrowthSignal:
    def test_defaults(self):
        g = GrowthSignal()
        assert g.detected is False
        assert g.multiplier_applied == 1.0

    def test_multiplier_below_1_rejected(self):
        with pytest.raises(ValidationError):
            GrowthSignal(multiplier_applied=0.5)

    def test_boost_valid(self):
        g = GrowthSignal(
            detected=True,
            description="self-taught, 0 to 3 production apps in 18 months",
            multiplier_applied=1.15,
        )
        assert g.multiplier_applied == 1.15


# ═══════════════════════════════════════════════════════════════════════════════
# CandidateVerdict — the output contract
# ═══════════════════════════════════════════════════════════════════════════════


def _dim(score: int) -> DimensionScore:
    """Helper: create a DimensionScore with placeholder evidence."""
    return DimensionScore(
        score=score, evidence=["test evidence"], rationale="test rationale"
    )


def _make_verdict(**overrides) -> dict:
    """Helper: build a valid CandidateVerdict kwargs dict, with optional overrides."""
    base = {
        "candidate_id": "test-001",
        "evaluated_for_role": "Senior Backend Engineer",
        "overall": 72,
        "verdict": "hire",
        "candidate_type": "promising",
        "dimensions": Dimensions(
            skill=_dim(80),
            hunger=_dim(90),
            creativity=_dim(70),
            job_fit=_dim(65),
            reliability=_dim(75),
        ),
        "pedigree_adjustment": PedigreeAdjustment(),
        "growth_signal": GrowthSignal(),
        "red_flags": [],
        "human_review_notes": "",
        "confidence": 0.85,
    }
    base.update(overrides)
    return base


class TestCandidateVerdict:
    def test_valid_verdict(self):
        v = CandidateVerdict(**_make_verdict())
        assert v.verdict == "hire"
        assert v.candidate_type == "promising"
        assert v.dimensions.skill.score == 80
        assert v.dimensions.hunger.score == 90
        assert v.confidence == 0.85

    def test_all_verdict_values_accepted(self):
        for val in ("strong_hire", "hire", "lean_hire", "hold", "pass"):
            v = CandidateVerdict(**_make_verdict(verdict=val))
            assert v.verdict == val

    def test_all_candidate_types_accepted(self):
        for val in ("promising", "polished", "both", "unclear"):
            v = CandidateVerdict(**_make_verdict(candidate_type=val))
            assert v.candidate_type == val

    def test_invalid_verdict_rejected(self):
        with pytest.raises(ValidationError):
            CandidateVerdict(**_make_verdict(verdict="definitely_hire"))

    def test_invalid_candidate_type_rejected(self):
        with pytest.raises(ValidationError):
            CandidateVerdict(**_make_verdict(candidate_type="genius"))

    def test_overall_above_100_rejected(self):
        with pytest.raises(ValidationError):
            CandidateVerdict(**_make_verdict(overall=150))

    def test_overall_below_0_rejected(self):
        with pytest.raises(ValidationError):
            CandidateVerdict(**_make_verdict(overall=-10))

    def test_confidence_above_1_rejected(self):
        with pytest.raises(ValidationError):
            CandidateVerdict(**_make_verdict(confidence=1.5))

    def test_confidence_below_0_rejected(self):
        with pytest.raises(ValidationError):
            CandidateVerdict(**_make_verdict(confidence=-0.1))

    def test_output_contract_json_shape(self):
        """
        Verify the serialized dict has EXACTLY the fields defined in
        Section 3 of the build directive. No missing, no extra.
        """
        v = CandidateVerdict(**_make_verdict())
        d = v.model_dump()

        # Top-level keys
        expected_top_keys = {
            "candidate_id",
            "evaluated_for_role",
            "overall",
            "verdict",
            "candidate_type",
            "dimensions",
            "pedigree_adjustment",
            "growth_signal",
            "red_flags",
            "human_review_notes",
            "confidence",
        }
        assert set(d.keys()) == expected_top_keys

        # Dimensions sub-keys
        assert set(d["dimensions"].keys()) == {
            "skill",
            "hunger",
            "creativity",
            "job_fit",
            "reliability",
        }
        for dim_name in ("skill", "hunger", "creativity", "job_fit", "reliability"):
            dim = d["dimensions"][dim_name]
            assert set(dim.keys()) == {"score", "evidence", "rationale"}

        # Pedigree adjustment sub-keys
        assert set(d["pedigree_adjustment"].keys()) == {
            "applied",
            "signals_found",
            "discount_factor",
            "net_score_change",
            "reason",
        }

        # Growth signal sub-keys
        assert set(d["growth_signal"].keys()) == {
            "detected",
            "description",
            "multiplier_applied",
        }

    def test_json_round_trip(self):
        """Serialize to JSON string, parse back, get identical model."""
        v1 = CandidateVerdict(**_make_verdict())
        json_str = v1.model_dump_json()
        v2 = CandidateVerdict.model_validate_json(json_str)
        assert v1 == v2


# ═══════════════════════════════════════════════════════════════════════════════
# RankingResult
# ═══════════════════════════════════════════════════════════════════════════════


class TestRankingResult:
    def test_valid_ranking(self):
        role = RoleSpec(**load_fixture("role_backend_senior.json"))
        verdict = CandidateVerdict(**_make_verdict())
        result = RankingResult(
            role=role,
            candidates=[RankedCandidate(rank=1, verdict=verdict)],
            total_evaluated=2,
            total_passed=1,
        )
        assert result.total_evaluated == 2
        assert result.total_passed == 1
        assert result.candidates[0].rank == 1

    def test_rank_zero_rejected(self):
        with pytest.raises(ValidationError):
            RankedCandidate(rank=0, verdict=CandidateVerdict(**_make_verdict()))
