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
    Maintains supervisor queue state for Stage 3.
    """
    
    def __init__(self):
        self.supervisor_queue: list[tuple[Candidate, RoleSpec]] = []
        self.approved_stream_a: list[Candidate] = []
        self.final_verdicts: list[CandidateVerdict] = []
        self.stz_promotions_count = 0
        self.l1_promotions_count = 0
        # We need to keep track of verdicts for stream c / fatal faults
        
    def reset(self):
        self.supervisor_queue.clear()
        self.approved_stream_a.clear()
        self.final_verdicts.clear()
        self.stz_promotions_count = 0
        self.l1_promotions_count = 0

    def run_batch(self, candidates: list[Candidate], role: RoleSpec):
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
                self.final_verdicts.append(generate_fail_verdict(candidate, role, "Failed Stage 1: Triage (Missing critical info)"))
                continue
                
            # STAGE 2: FATAL FAULT CHECK
            if check_fatal_faults(candidate, role):
                self.final_verdicts.append(generate_fail_verdict(candidate, role, "Failed Stage 2: Fatal Faults (CTC/Notice/Location)"))
                continue
                
            if stream == "stream_a":
                # STAGE 3: SUPERVISOR GATE (Pending)
                self.supervisor_queue.append((candidate, role))
            else:
                # STAGE 4: LEVEL 1 SCORING (Stream B)
                l1_verdict = evaluate_candidate(candidate, role)
                if l1_verdict.overall >= 70:
                    self.approved_stream_a.append(candidate)
                    self.l1_promotions_count += 1
                else:
                    # STAGE 5: SPECIAL TEST ZONE
                    if candidate.behavioral:
                        resp_rate = candidate.behavioral.response_rate
                        avg_time = candidate.behavioral.avg_response_time_hours
                        if resp_rate > 0.9 and avg_time is not None and avg_time < 24:
                            self.approved_stream_a.append(candidate)
                            self.stz_promotions_count += 1
                            continue
                    
                    self.final_verdicts.append(generate_fail_verdict(candidate, role, "Failed Stage 5: Special Test Zone"))

    def resolve_supervisor_decision(self, candidate_id: str, approved: bool):
        """
        Process a decision from the supervisor gate for a specific candidate.
        """
        for i, (cand, role) in enumerate(self.supervisor_queue):
            if cand.id == candidate_id:
                self.supervisor_queue.pop(i)
                if approved:
                    self.approved_stream_a.append(cand)
                else:
                    self.final_verdicts.append(generate_fail_verdict(cand, role, "Failed Stage 3: Supervisor Gate (Rejected by Human)"))
                return True
        return False

    def finalize_battle(self, role: RoleSpec) -> RankingResult:
        """
        STAGE 6: LEVEL 2 BATTLE
        Evaluates all approved Stream A candidates, sorts them, and applies seat constraints.
        Returns the final RankingResult including all rejected candidates.
        """
        # Precompute batch semantics for speed
        try:
            import numpy as np
            from meritengine.core.scoring.job_fit import get_embedding_model
            model = get_embedding_model()
            if model != "fallback" and model is not None and len(self.approved_stream_a) > 0:
                candidate_texts = []
                for c in self.approved_stream_a:
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
                
                for idx, c in enumerate(self.approved_stream_a):
                    c._semantic_fit_score = float(similarities[idx])
        except Exception:
            pass

        # Evaluate all battle contenders
        battle_verdicts = [evaluate_candidate(c, role) for c in self.approved_stream_a]
        
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
                
        all_verdicts = battle_verdicts + self.final_verdicts
        # Re-sort everyone to have a deterministic output (passed candidates at the bottom)
        all_verdicts.sort(key=lambda v: (-v.overall, v.candidate_id))
        
        ranked = [
            RankedCandidate(rank=i, verdict=v)
            for i, v in enumerate(all_verdicts, start=1)
        ]
        
        total_evaluated = len(all_verdicts) + len(self.supervisor_queue)
        total_passed = sum(1 for v in all_verdicts if v.verdict != "pass")
        
        return RankingResult(
            role=role,
            candidates=ranked,
            total_evaluated=total_evaluated,
            total_passed=total_passed
        )

# Global router instance for the application
global_router = PipelineRouter()
