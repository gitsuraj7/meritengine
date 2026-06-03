"""
MeritEngine — Domain Models (Pydantic v2)

Every data structure the system touches is defined here.
No business logic. No scoring. Just the contract.

Three model families:
  1. INPUT  — Candidate, RoleSpec, and their sub-models
  2. OUTPUT — CandidateVerdict and the dimension/adjustment models it contains
  3. SHARED — Evidence, enums, type aliases
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED TYPES
# ═══════════════════════════════════════════════════════════════════════════════

Verdict = Literal["strong_hire", "hire", "lean_hire", "hold", "pass"]
CandidateType = Literal["promising", "polished", "both", "unclear"]
Seniority = Literal["junior", "mid", "senior", "staff", "lead", "principal"]
Environment = Literal["startup", "scaleup", "enterprise", "agency"]
SkillPriority = Literal["must_have", "nice_to_have"]
ProjectStatus = Literal["completed", "in_progress", "abandoned"]


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT MODELS — Candidate
# ═══════════════════════════════════════════════════════════════════════════════


class Education(BaseModel):
    """One education entry. `is_tier1` flags pedigree institutions (IIT, MIT, etc.)."""

    institution: str
    degree: str  # e.g. "B.Tech", "Self-taught", "Bootcamp", "PhD"
    field: str  # e.g. "Computer Science", "Mechanical Engineering"
    graduation_year: int | None = None
    is_tier1: bool = False  # pedigree flag — scorer reads this


class WorkExperience(BaseModel):
    """One work stint. `is_faang_or_brand` flags pedigree employers."""

    company: str
    title: str
    duration_months: int = Field(ge=0)
    description: str = ""
    is_faang_or_brand: bool = False  # pedigree flag — scorer reads this


class GitHubRepo(BaseModel):
    """A single repository from a candidate's GitHub profile."""

    name: str
    description: str = ""
    stars: int = Field(default=0, ge=0)
    forks: int = Field(default=0, ge=0)
    total_commits: int = Field(default=0, ge=0)
    languages: list[str] = []
    is_production: bool = False  # deployed / used by real users
    is_fork: bool = False
    last_commit_date: date | None = None


class GitHubProfile(BaseModel):
    """Aggregate GitHub presence."""

    username: str
    total_repos: int = Field(default=0, ge=0)
    total_commits_last_year: int = Field(default=0, ge=0)
    contribution_streak_days: int = Field(default=0, ge=0)
    repos: list[GitHubRepo] = []


class Assessment(BaseModel):
    """Take-home / coding challenge result."""

    submitted: bool = False
    score: float | None = Field(default=None, ge=0, le=100)
    approach_description: str = ""
    is_unconventional: bool = False  # non-template solution
    is_working: bool = False  # does it actually run?
    time_taken_minutes: int | None = Field(default=None, ge=0)


class BehavioralSignals(BaseModel):
    """Async communication and follow-through metrics."""

    response_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_response_time_hours: float | None = Field(default=None, ge=0)
    communication_clarity: float = Field(default=0.0, ge=0.0, le=1.0)
    follow_through_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class SideProject(BaseModel):
    """A self-reported side project or portfolio piece."""

    name: str
    description: str = ""
    url: str | None = None
    status: ProjectStatus = "completed"
    technologies: list[str] = []


class Candidate(BaseModel):
    """
    Complete candidate profile — the unit of input to the pipeline.

    Fields are intentionally nullable/defaulted so the system degrades
    gracefully on incomplete data (and flags low confidence accordingly).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    name: str
    email: str = ""

    # Skills — self-reported, NOT treated as ground truth
    skills_claimed: list[str] = []

    # Background
    education: list[Education] = []
    work_experience: list[WorkExperience] = []
    total_experience_months: int = Field(default=0, ge=0)

    # Demonstrated work signals
    github: GitHubProfile | None = None
    assessment: Assessment | None = None
    side_projects: list[SideProject] = []

    # Behavioral / communication
    behavioral: BehavioralSignals | None = None

    # Freeform text
    bio: str = ""
    resume_text: str = ""  # raw resume text for semantic matching

    # Compensation & logistics
    current_ctc: float | None = Field(default=None, ge=0)
    expected_ctc: float | None = Field(default=None, ge=0)
    notice_period_days: int | None = Field(default=None, ge=0)
    location: str = ""
    willing_to_relocate: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT MODELS — RoleSpec (parsed Job Description)
# ═══════════════════════════════════════════════════════════════════════════════


class SkillRequirement(BaseModel):
    """A single skill required or preferred for the role."""

    name: str
    priority: SkillPriority = "must_have"
    min_years: int | None = Field(default=None, ge=0)


class RoleSpec(BaseModel):
    """
    Structured representation of a Job Description.

    Produced by ingest/role_parser.py from raw JD text.
    Consumed by every scorer to assess role-specific fit.
    """

    title: str
    department: str = ""
    seniority: Seniority = "mid"
    required_skills: list[SkillRequirement] = []
    domain: str = ""  # e.g. "fintech", "healthcare", "e-commerce"
    environment: Environment = "startup"
    min_experience_months: int = Field(default=0, ge=0)
    max_experience_months: int | None = Field(default=None, ge=0)
    budget_max_ctc: float | None = Field(default=None, ge=0)
    location: str = ""
    remote_ok: bool = True
    culture_signals: list[str] = []  # e.g. ["fast-paced", "ownership"]
    raw_jd_text: str = ""
    key_responsibilities: list[str] = []
    
    # New routing pipeline constraints
    direct_seats: int = Field(default=0, ge=0)
    waitlist_seats: int = Field(default=0, ge=0)
    backup_seats: int = Field(default=0, ge=0)
    max_notice_period_days: int | None = Field(default=None, ge=0)


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT MODELS — Evaluation result
# ═══════════════════════════════════════════════════════════════════════════════


class DimensionScore(BaseModel):
    """
    Score for a single evaluation dimension.
    Every score MUST have evidence and rationale or it is invalid output.
    """

    score: int = Field(ge=0, le=100)
    evidence: list[str]
    rationale: str


class Dimensions(BaseModel):
    """All five scoring dimensions for a candidate evaluation."""

    skill: DimensionScore
    hunger: DimensionScore
    creativity: DimensionScore
    job_fit: DimensionScore
    reliability: DimensionScore


class PedigreeAdjustment(BaseModel):
    """
    Record of anti-bias pedigree dampening applied to a candidate.
    Logged in every output for auditability — even when not applied.
    """

    applied: bool = False
    signals_found: list[str] = []
    discount_factor: float = Field(default=0.3, ge=0.0, le=1.0)
    net_score_change: float = 0.0
    reason: str = ""


class GrowthSignal(BaseModel):
    """
    Detected growth trajectory signal.
    multiplier_applied >= 1.0 — growth can only boost, never penalize.
    """

    detected: bool = False
    description: str = ""
    multiplier_applied: float = Field(default=1.0, ge=1.0)


class CandidateVerdict(BaseModel):
    """
    The complete evaluation output for one candidate against one role.

    This is the OUTPUT CONTRACT from Section 3 of the build directive.
    Every field is mandatory. Scores without evidence are invalid.
    """

    candidate_id: str
    evaluated_for_role: str  # role title from RoleSpec
    overall: int = Field(ge=0, le=100)
    verdict: Verdict
    candidate_type: CandidateType
    dimensions: Dimensions
    pedigree_adjustment: PedigreeAdjustment
    growth_signal: GrowthSignal
    red_flags: list[str] = []
    human_review_notes: str = ""
    confidence: float = Field(ge=0.0, le=1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# RANKING OUTPUT — list-level result
# ═══════════════════════════════════════════════════════════════════════════════


class RankedCandidate(BaseModel):
    """A single entry in the ranked output list."""

    rank: int = Field(ge=1)
    verdict: CandidateVerdict


class RankingResult(BaseModel):
    """Complete output of a ranking run: role + ordered candidates."""

    role: RoleSpec
    candidates: list[RankedCandidate]
    total_evaluated: int = Field(ge=0)
    total_passed: int = Field(ge=0)  # verdict != "pass"
