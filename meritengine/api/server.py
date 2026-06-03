"""
meritengine/api/server.py — FastAPI Application Server

Exposes candidates evaluation and batch ranking pipelines via HTTP endpoints.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from meritengine.core.models import Candidate, CandidateVerdict, RankingResult, RoleSpec
from meritengine.core.pipeline import evaluate_candidate, rank_candidates
from meritengine.core.explain import generate_explanation
from meritengine.core.router import global_router
from meritengine.core import db

# Ensure DB is initialized on startup
db.init_db()

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

class PipelineRunRequest(BaseModel):
    candidates: list[Candidate]
    role: RoleSpec
    webhook_url: str = ""

class SupervisorDecisionRequest(BaseModel):
    candidate_id: str
    approved: bool


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


# ---------------------------------------------------------
# NEW MULTI-TIER ROUTING ENDPOINTS
# ---------------------------------------------------------

@app.post("/pipeline/run", tags=["Pipeline"])
def pipeline_run(request: PipelineRunRequest):
    """Processes a batch of candidates up to the supervisor gate."""
    global_router.run_batch(request.candidates, request.role, request.webhook_url)
    return {"status": "batch_processed", "total_candidates": len(request.candidates)}

@app.get("/supervisor/queue", tags=["Supervisor"])
def get_supervisor_queue():
    """Fetches candidates currently stuck at the supervisor gate."""
    queue = db.get_supervisor_queue()
    return [{"candidate": c, "role": r, "webhook_url": w} for c, r, w in queue]

@app.post("/supervisor/decision", tags=["Supervisor"])
def supervisor_decision(request: SupervisorDecisionRequest):
    """Human-in-the-loop decision endpoint that also fires the async webhook."""
    success = global_router.resolve_supervisor_decision(request.candidate_id, request.approved)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found in pending queue.")
    return {"status": "decision_recorded", "candidate_id": request.candidate_id, "approved": request.approved}

@app.post("/pipeline/finalize_battle", response_model=RankingResult, tags=["Pipeline"])
def finalize_battle(role: RoleSpec):
    """Triggers Stage 6: The Level 2 Battle over all approved candidates."""
    approved = db.get_approved_for_battle()
    if not approved:
        raise HTTPException(status_code=400, detail={"error": "no_approved_candidates", "message": "No candidates have cleared the supervisor gate yet."})
    
    result = global_router.finalize_battle(role)
    
    # Generate explanations for battle survivors
    # We map candidate IDs back to candidate objects for explain.py
    approved_map = {c.id: c for c, r in approved}
    for ranked in result.candidates:
        cand = approved_map.get(ranked.verdict.candidate_id)
        if cand:
            generate_explanation(ranked.verdict, cand)
            
    return result

@app.post("/pipeline/reset", tags=["Pipeline"])
def reset_pipeline():
    """Wipes the pipeline and SQLite DB for demo purposes."""
    global_router.reset()
    return {"status": "reset_successful"}

import json

@app.get("/fixtures/{name}", tags=["System"])
def get_fixture(name: str):
    """Returns a test fixture JSON to be used by the UI simulator."""
    fixture_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "fixtures", f"{name}.json")
    if not os.path.exists(fixture_path):
        raise HTTPException(status_code=404, detail="Fixture not found")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------
# UI MOUNT (Must be last)
# ---------------------------------------------------------

ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
os.makedirs(ui_dir, exist_ok=True)

# Create index.html if it doesn't exist to prevent crash
if not os.path.exists(os.path.join(ui_dir, "index.html")):
    with open(os.path.join(ui_dir, "index.html"), "w") as f:
        f.write("<h1>MeritEngine UI Loading...</h1>")

app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
