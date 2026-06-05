"""
meritengine/core/pipeline.py — Pipeline Orchestrator

Wires the ingestion layer inputs, all 5 dimension scorers, and aggregation
logic into single-candidate evaluation and batch ranking pipelines.
"""

from meritengine.core.models import (
    Candidate,
    CandidateVerdict,
    Dimensions,
    RankedCandidate,
    RankingResult,
    RoleSpec,
)
from meritengine.core.scoring.aggregate import aggregate_scores
from meritengine.core.scoring.creativity import evaluate_creativity
from meritengine.core.scoring.hunger import evaluate_hunger
from meritengine.core.scoring.job_fit import evaluate_job_fit
from meritengine.core.scoring.reliability import evaluate_reliability
from meritengine.core.scoring.skill import evaluate_skill


from meritengine.core.scoring.committee import CommitteeEvaluator


def evaluate_candidate(candidate: Candidate, role: RoleSpec) -> CandidateVerdict:
    """
    Evaluates a single candidate against a role specification by routing
    to all 5 dimension scorers and combining them via aggregate_scores.
    Then enriches and humanizes the score using the 50-agent committee.
    """
    skill = evaluate_skill(candidate, role)
    hunger = evaluate_hunger(candidate, role)
    creativity = evaluate_creativity(candidate, role)
    job_fit = evaluate_job_fit(candidate, role)
    reliability = evaluate_reliability(candidate, role)

    dimensions = Dimensions(
        skill=skill,
        hunger=hunger,
        creativity=creativity,
        job_fit=job_fit,
        reliability=reliability,
    )

    verdict = aggregate_scores(candidate, role, dimensions)

    # Empathy-First 50-agent Committee Scoring
    committee = CommitteeEvaluator()
    committee_result = committee.evaluate(candidate, role)

    # Soft humanized boost representing committee advocacy
    boost_val = committee_result["score_boost"]
    advocacy_boost = min(15, int(boost_val / 10))
    verdict.overall = min(100, verdict.overall + advocacy_boost)

    # Re-map verdict category based on boosted score
    if verdict.overall >= 85:
        verdict.verdict = "strong_hire"
    elif verdict.overall >= 70:
        verdict.verdict = "hire"
    elif verdict.overall >= 55:
        verdict.verdict = "lean_hire"
    elif verdict.overall >= 40:
        verdict.verdict = "hold"
    else:
        verdict.verdict = "pass"

    # Construct the humanized advocacy narrative
    advocacy_bullets = "\n".join(f"- {note}" for note in committee_result["advocacy_notes"][:6])
    verdict.human_review_notes = (
        f"=== EMPATHETIC COMMITTEE ADVOCACY NARRATIVE ===\n"
        f"Our 50-agent committee evaluated this builder and noted the following human signals:\n"
        f"{advocacy_bullets}\n\n"
        f"Ombudsman Verdict: Prioritize their demonstrated builder drive over traditional pedigree."
    )

    return verdict


def rank_candidates(candidates: list[Candidate], role: RoleSpec) -> RankingResult:
    """
    Evaluates a batch of candidates, ranks them by overall score descending,
    and returns a structured RankingResult.
    """
    # Precompute semantic similarity scores in batch to speed up processing
    try:
        import numpy as np
        from meritengine.core.scoring.job_fit import get_embedding_model
        model = get_embedding_model()
        if model != "fallback" and model is not None and len(candidates) > 0:
            candidate_texts = []
            for c in candidates:
                candidate_text = f"{c.bio} {c.resume_text} " + " ".join(
                    exp.description for exp in c.work_experience
                )
                candidate_texts.append(candidate_text)
            
            role_text = f"{role.title} {role.domain} " + " ".join(role.key_responsibilities) + f" {role.raw_jd_text}"
            
            # Encode everything in a single batch
            all_embeddings = model.encode(candidate_texts + [role_text])
            candidate_embeddings = all_embeddings[:-1]
            role_embedding = all_embeddings[-1]
            
            # Vectorized cosine similarity computation
            norms_candidates = np.linalg.norm(candidate_embeddings, axis=1)
            norm_role = np.linalg.norm(role_embedding)
            
            norms_candidates[norms_candidates == 0] = 1.0
            if norm_role == 0:
                norm_role = 1.0
                
            dots = np.dot(candidate_embeddings, role_embedding)
            similarities = dots / (norms_candidates * norm_role)
            
            # Attach similarities to candidates
            for idx, c in enumerate(candidates):
                c._semantic_fit_score = float(similarities[idx])
    except Exception:
        pass

    verdicts = [evaluate_candidate(c, role) for c in candidates]

    # Sort descending by overall score, tie-break by candidate_id for stability
    sorted_verdicts = sorted(verdicts, key=lambda v: (-v.overall, v.candidate_id))

    ranked_candidates = [
        RankedCandidate(rank=idx, verdict=v)
        for idx, v in enumerate(sorted_verdicts, start=1)
    ]

    total_passed = sum(1 for v in verdicts if v.verdict != "pass")

    return RankingResult(
        role=role,
        candidates=ranked_candidates,
        total_evaluated=len(candidates),
        total_passed=total_passed,
    )
