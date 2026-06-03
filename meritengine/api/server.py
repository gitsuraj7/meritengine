"""
meritengine/api/server.py — FastAPI Application Server

Exposes candidates evaluation and batch ranking pipelines via HTTP endpoints.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from meritengine.core.models import Candidate, CandidateVerdict, RankingResult, RoleSpec
from meritengine.core.pipeline import evaluate_candidate, rank_candidates
from meritengine.core.explain import generate_explanation

app = FastAPI(
    title="MeritEngine API",
    description="Intelligent candidate evaluation and ranking engine prioritizing demonstrated reality.",
    version="1.0.0",
)


class EvaluateRequest(BaseModel):
    candidate: Candidate
    role: RoleSpec


class RankRequest(BaseModel):
    candidates: list[Candidate]
    role: RoleSpec


@app.get("/health", tags=["System"])
def health_check():
    """Simple check validating API service availability."""
    return {"status": "healthy", "service": "meritengine"}


@app.post("/evaluate", response_model=CandidateVerdict, tags=["Evaluation"])
def evaluate(request: EvaluateRequest):
    """
    Evaluates a single candidate against a role, applying anti-bias dampening
    and growth boosts, and returns an enriched explainable verdict.
    """
    verdict = evaluate_candidate(request.candidate, request.role)
    verdict = generate_explanation(verdict, request.candidate)
    return verdict


@app.post("/rank", response_model=RankingResult, tags=["Evaluation"])
def rank(request: RankRequest):
    """
    Evaluates and ranks a list of candidates against a target role spec,
    returning a sorted list with detailed verdicts and explanation sheets.
    """
    result = rank_candidates(request.candidates, request.role)
    
    # Enrich each verdict inside the ranked list with explanations
    for ranked_candidate in result.candidates:
        candidate_obj = next(
            (c for c in request.candidates if c.id == ranked_candidate.verdict.candidate_id),
            None
        )
        if candidate_obj:
            generate_explanation(ranked_candidate.verdict, candidate_obj)
            
    return result
