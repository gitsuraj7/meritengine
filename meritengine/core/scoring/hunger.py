"""
meritengine/core/scoring/hunger.py — Hunger Scorer

Evaluates candidates on grit, contribution velocity, and communication urgency.
"""

from meritengine.core.models import Candidate, DimensionScore, RoleSpec


def evaluate_hunger(candidate: Candidate, role: RoleSpec) -> DimensionScore:
    """
    Scores hunger (0-100) based on contribution velocity, responsiveness,
    and self-directed project cadence.
    """
    evidence: list[str] = []
    score = 0.0

    # 1. GitHub contribution cadence (40%)
    if candidate.github:
        commits = candidate.github.total_commits_last_year
        streak = candidate.github.contribution_streak_days
        
        # Commits sub-score (max 25)
        if commits >= 800:
            commit_points = 25.0
        elif commits >= 400:
            commit_points = 18.0
        elif commits >= 100:
            commit_points = 10.0
        else:
            commit_points = 5.0
            
        # Streak sub-score (max 15)
        streak_points = min(streak / 5.0, 15.0)
        
        github_contrib = commit_points + streak_points
        score += github_contrib
        evidence.append(
            f"Active GitHub footprint: {commits} commits last year, longest active streak of {streak} days."
        )
    else:
        evidence.append("No active public GitHub commit signals found.")

    # 2. Behavioral responsiveness (30%)
    if candidate.behavioral:
        resp_rate = candidate.behavioral.response_rate
        avg_time = candidate.behavioral.avg_response_time_hours
        
        # Response rate points (max 15)
        resp_rate_points = resp_rate * 15.0
        
        # Avg response time points (max 15)
        if avg_time is not None:
            if avg_time <= 4.0:
                resp_time_points = 15.0
            elif avg_time <= 12.0:
                resp_time_points = 10.0
            elif avg_time <= 24.0:
                resp_time_points = 5.0
            else:
                resp_time_points = 1.0
        else:
            resp_time_points = 5.0

        behavioral_contrib = resp_rate_points + resp_time_points
        score += behavioral_contrib
        evidence.append(
            f"Urgency metrics: response rate is {resp_rate * 100:.0f}% with average response time of "
            f"{avg_time if avg_time is not None else 'N/A'} hours."
        )
    else:
        evidence.append("No async communication metrics available to evaluate outreach responsiveness.")

    # 3. Independent side-project cadence (30%)
    if candidate.side_projects:
        project_count = len(candidate.side_projects)
        active_count = sum(1 for p in candidate.side_projects if p.status in ("completed", "in_progress"))
        
        proj_points = min(active_count * 10.0, 30.0)
        score += proj_points
        evidence.append(
            f"Shipped/actively shipping {active_count} self-directed side projects."
        )
    else:
        evidence.append("No independent side projects or portfolio artifacts submitted.")

    final_score = int(round(score))
    
    if final_score >= 80:
        rationale = "High hunger. Exhibits remarkable shipping frequency, active coding cadence, and prompt communications."
    elif final_score >= 50:
        rationale = "Moderate hunger. Showcases healthy contribution velocity and standard communication responsiveness."
    else:
        rationale = "Low demonstrated hunger. Lacks active public git traces, recent side projects, or prompt response history."

    return DimensionScore(
        score=final_score,
        evidence=evidence,
        rationale=rationale,
    )
