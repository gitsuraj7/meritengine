from __future__ import annotations

from typing import Literal

from meritengine.core.models import (
    Candidate,
    CandidateVerdict,
    RoleSpec,
    RankedCandidate,
    RankingResult,
    Dimensions,
    DimensionScore,
    PedigreeAdjustment,
    GrowthSignal,
)
from meritengine.core.pipeline import evaluate_candidate
from meritengine.core import db
import httpx
import threading

StreamType = Literal["stream_a", "stream_b", "stream_c"]

def triage(candidate: Candidate) -> StreamType:
    """
    STAGE 1: INITIAL TRIAGE
    Classify every incoming candidate into exactly one of three streams.
    """
    # Stream C Check
    if not candidate.name or not candidate.email or not candidate.resume_text.strip():
        return "stream_c"

    # Stream A Check
    github_repos_count = len(candidate.github.repos) if candidate.github else 0
    has_completed_side_project = any(
        sp.status == "completed" for sp in candidate.side_projects
    )
    if github_repos_count >= 2 and has_completed_side_project:
        return "stream_a"

    # Otherwise Stream B
    return "stream_b"

def check_fatal_faults(candidate: Candidate, role: RoleSpec) -> bool:
    """
    STAGE 2: FATAL FAULT CHECK
    Applies to Streams A and B. Hard constraints on RoleSpec.
    Returns True if a fatal fault is found.
    """
    if role.budget_max_ctc and candidate.current_ctc and candidate.current_ctc > role.budget_max_ctc:
        return True

    if role.max_notice_period_days is not None and candidate.notice_period_days is not None:
        if candidate.notice_period_days > role.max_notice_period_days:
            return True

    if role.location and candidate.location:
        # Simple case-insensitive match for location
        if role.location.lower() not in candidate.location.lower() and candidate.location.lower() not in role.location.lower():
            if not candidate.willing_to_relocate:
                return True

    return False

def generate_fail_verdict(candidate: Candidate, role: RoleSpec, reason: str = "Rejected by routing pipeline") -> CandidateVerdict:
    empty_dim = DimensionScore(score=0, evidence=[reason], rationale=reason)
    return CandidateVerdict(
        candidate_id=candidate.id,
        evaluated_for_role=role.title,
        overall=0,
        verdict="pass",
        candidate_type="unclear",
        dimensions=Dimensions(
            skill=empty_dim,
            hunger=empty_dim,
            creativity=empty_dim,
            job_fit=empty_dim,
            reliability=empty_dim,
        ),
        pedigree_adjustment=PedigreeAdjustment(),
        growth_signal=GrowthSignal(),
        red_flags=[reason],
        confidence=1.0,
    )

class PipelineRouter:
    """
    Orchestrates the multi-tier routing pipeline.
    Uses SQLite db for persistence instead of in-memory queues.
    """
    
    def __init__(self):
        self.stz_promotions_count = 0
        self.l1_promotions_count = 0
        
    def reset(self):
        db.reset_db()
        self.stz_promotions_count = 0
        self.l1_promotions_count = 0

    def run_batch(self, candidates: list[Candidate], role: RoleSpec, webhook_url: str = ""):
        """
        Processes a batch of candidates up to the supervisor gate or final battle.
        For candidates needing supervisor approval (Stream A), they are added to the queue.
        For Stream B, they are routed through L1 and potentially STZ, and if they pass,
        they skip supervisor gate and go directly to approved_stream_a.
        """
        
        for candidate in candidates:
            # STAGE 1: TRIAGE
            stream = triage(candidate)
            
            if stream == "stream_c":
                verdict = generate_fail_verdict(candidate, role, "Failed Stage 1: Triage (Missing critical info)")
                db.save_final_verdict(candidate.id, verdict)
                continue
                
            # STAGE 2: FATAL FAULT CHECK
            if check_fatal_faults(candidate, role):
                verdict = generate_fail_verdict(candidate, role, "Failed Stage 2: Fatal Faults (CTC/Notice/Location)")
                db.save_final_verdict(candidate.id, verdict)
                continue
                
            if stream == "stream_a":
                # STAGE 3: SUPERVISOR GATE (Pending)
                db.add_to_supervisor_queue(candidate, role, webhook_url)
            else:
                # STAGE 4: LEVEL 1 SCORING (Stream B)
                l1_verdict = evaluate_candidate(candidate, role)
                if l1_verdict.overall >= 70:
                    db.update_candidate_status(candidate.id, "approved_for_battle")
                    self.l1_promotions_count += 1
                else:
                    # STAGE 5: SPECIAL TEST ZONE
                    if candidate.behavioral:
                        resp_rate = candidate.behavioral.response_rate
                        avg_time = candidate.behavioral.avg_response_time_hours
                        if resp_rate > 0.9 and avg_time is not None and avg_time < 24:
                            db.update_candidate_status(candidate.id, "approved_for_battle")
                            self.stz_promotions_count += 1
                            continue
                    
                    verdict = generate_fail_verdict(candidate, role, "Failed Stage 5: Special Test Zone")
                    db.save_final_verdict(candidate.id, verdict)

    def _trigger_webhook(self, url: str, payload: dict):
        if not url:
            return
        def fire():
            try:
                # Simple static webhook secret as per plan
                headers = {"X-MeritEngine-Signature": "hackathon-demo-secret"}
                httpx.post(url, json=payload, headers=headers, timeout=5.0)
            except Exception as e:
                print(f"Webhook failed: {e}")
        threading.Thread(target=fire).start()

    def resolve_supervisor_decision(self, candidate_id: str, approved: bool):
        """
        Process a decision from the supervisor gate for a specific candidate.
        """
        pending = db.get_pending_candidate(candidate_id)
        if not pending:
            return False
        
        c, r, webhook = pending
        
        if approved:
            db.update_candidate_status(candidate_id, "approved_for_battle")
            self._trigger_webhook(webhook, {"candidate_id": candidate_id, "status": "approved_for_battle"})
        else:
            verdict = generate_fail_verdict(c, r, "Failed Stage 3: Supervisor Gate (Rejected by Human)")
            db.save_final_verdict(candidate_id, verdict)
            self._trigger_webhook(webhook, {"candidate_id": candidate_id, "status": "rejected", "verdict": verdict.model_dump()})
            
        return True

    def finalize_battle(self, role: RoleSpec) -> RankingResult:
        """
        STAGE 6: LEVEL 2 BATTLE
        Evaluates all approved Stream A candidates, sorts them, and applies seat constraints.
        Returns the final RankingResult including all rejected candidates.
        """
        approved_stream = db.get_approved_for_battle()
        approved_candidates = [t[0] for t in approved_stream]
        
        # Precompute batch semantics for speed
        try:
            import numpy as np
            from meritengine.core.scoring.job_fit import get_embedding_model
            model = get_embedding_model()
            if model != "fallback" and model is not None and len(approved_candidates) > 0:
                candidate_texts = []
                for c in approved_candidates:
                    candidate_text = f"{c.bio} {c.resume_text} " + " ".join(
                        exp.description for exp in c.work_experience
                    )
                    candidate_texts.append(candidate_text)
                
                role_text = f"{role.title} {role.domain} " + " ".join(role.key_responsibilities) + f" {role.raw_jd_text}"
                all_embeddings = model.encode(candidate_texts + [role_text])
                candidate_embeddings = all_embeddings[:-1]
                role_embedding = all_embeddings[-1]
                
                norms_candidates = np.linalg.norm(candidate_embeddings, axis=1)
                norm_role = np.linalg.norm(role_embedding)
                norms_candidates[norms_candidates == 0] = 1.0
                if norm_role == 0: norm_role = 1.0
                    
                dots = np.dot(candidate_embeddings, role_embedding)
                similarities = dots / (norms_candidates * norm_role)
                
                for idx, c in enumerate(approved_candidates):
                    c._semantic_fit_score = float(similarities[idx])
        except Exception:
            pass

        # Evaluate all battle contenders
        battle_verdicts = [evaluate_candidate(c, role) for c in approved_candidates]
        
        # Sort descending by overall score
        battle_verdicts.sort(key=lambda v: (-v.overall, v.candidate_id))
        
        # Apply seat constraints
        direct = role.direct_seats
        waitlist = role.waitlist_seats
        backup = role.backup_seats
        
        for idx, verdict in enumerate(battle_verdicts):
            if idx < direct:
                verdict.verdict = "strong_hire"
            elif idx < direct + waitlist:
                verdict.verdict = "hire"
            elif idx < direct + waitlist + backup:
                verdict.verdict = "lean_hire"
            else:
                verdict.verdict = "pass"
                
        # Save battle verdicts to DB
        db.save_batch_final_verdicts(battle_verdicts)
                
        # Fetch all final verdicts from DB to include fast-failed ones
        all_verdicts = db.get_all_finished_verdicts()
        
        # Re-sort everyone to have a deterministic output (passed candidates at the bottom)
        all_verdicts.sort(key=lambda v: (-v.overall, v.candidate_id))
        
        ranked = [
            RankedCandidate(rank=i, verdict=v)
            for i, v in enumerate(all_verdicts, start=1)
        ]
        
        total_evaluated = len(all_verdicts) + len(db.get_supervisor_queue())
        total_passed = sum(1 for v in all_verdicts if v.verdict != "pass")
        
        return RankingResult(
            role=role,
            candidates=ranked,
            total_evaluated=total_evaluated,
            total_passed=total_passed
        )

# Global router instance for the application
global_router = PipelineRouter()
