"""
meritengine/core/scoring/reliability.py — Reliability Scorer

Evaluates follow-through, task completion, and execution consistency.
"""

from meritengine.core.models import Candidate, DimensionScore, RoleSpec


def evaluate_reliability(candidate: Candidate, role: RoleSpec) -> DimensionScore:
    """
    Scores reliability (0-100) based on task follow-through rate, communication response rate,
    side-project completion ratio, and whether their assessment was verified as working.
    """
    evidence: list[str] = []
    score = 0.0

    # 1. Behavioral follow-through and response rates (40%)
    if candidate.behavioral:
        ft_rate = candidate.behavioral.follow_through_rate
        resp_rate = candidate.behavioral.response_rate
        
        # Follow-through (max 25)
        ft_points = ft_rate * 25.0
        # Response rate (max 15)
        resp_points = resp_rate * 15.0
        
        score += ft_points + resp_points
        evidence.append(
            f"Commitment metrics: follow-through rate is {ft_rate*100:.0f}%, "
            f"response rate is {resp_rate*100:.0f}%."
        )
    else:
        # Default baseline if missing communication metrics
        score += 20.0
        evidence.append("No behavioral commitment metrics recorded; defaulting to baseline reliability.")

    # 2. Side-project completion ratio (30%)
    if candidate.side_projects:
        total_projects = len(candidate.side_projects)
        completed_projects = sum(1 for p in candidate.side_projects if p.status == "completed")
        
        ratio = completed_projects / total_projects
        proj_points = ratio * 30.0
        score += proj_points
        evidence.append(
            f"Project execution: completed {completed_projects} of {total_projects} side projects "
            f"({ratio*100:.0f}% completion rate)."
        )
    else:
        score += 15.0
        evidence.append("No side projects provided to evaluate completion behavior.")

    # 3. Assessment execution state (30%)
    if candidate.assessment:
        if candidate.assessment.submitted:
            if candidate.assessment.is_working:
                score += 30.0
                evidence.append("Verifiable execution: take-home challenge solution compiled and executed cleanly.")
            else:
                evidence.append("Technical risk: submitted take-home challenge solution failed execution check.")
        else:
            evidence.append("Assessment state: challenge not submitted.")
    else:
        # If no assessment is required, default to standard mid points
        score += 15.0
        evidence.append("No coding assessment submitted.")

    final_score = int(round(score))
    
    if final_score >= 80:
        rationale = "High reliability. Demonstrates exceptional follow-through, active delivery rates, and verified technical execution."
    elif final_score >= 50:
        rationale = "Moderate reliability. Exhibits standard completion behavior but shows some execution or follow-through gaps."
    else:
        rationale = "Low reliability. Multiple execution risks detected: failed assessment checks or low behavioral follow-through rates."

    return DimensionScore(
        score=final_score,
        evidence=evidence,
        rationale=rationale,
    )
