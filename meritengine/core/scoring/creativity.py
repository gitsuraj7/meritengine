"""
meritengine/core/scoring/creativity.py — Creativity Scorer

Evaluates candidates on non-template solutions, open-source work, and unique builds.
"""

from meritengine.core.models import Candidate, DimensionScore, RoleSpec


def evaluate_creativity(candidate: Candidate, role: RoleSpec) -> DimensionScore:
    """
    Scores creativity (0-100) based on coding architecture diversity,
    unconventional assessment solutions, open-source forks, and popular repo stars.
    """
    evidence: list[str] = []
    score = 0.0

    # 1. Unconventional assessment solution (40%)
    if candidate.assessment and candidate.assessment.submitted:
        if candidate.assessment.is_unconventional:
            score += 40.0
            evidence.append(
                f"Coding assessment demonstrated a creative architectural approach: {candidate.assessment.approach_description}"
            )
        else:
            evidence.append("Coding assessment followed a standard/conventional solution template.")
    else:
        evidence.append("No technical coding assessment submitted to evaluate architectural design patterns.")

    # 2. Open-source contribution & repository impact (40%)
    if candidate.github:
        has_forks = any(repo.is_fork for repo in candidate.github.repos)
        max_stars = max((repo.stars for repo in candidate.github.repos), default=0)
        
        # Open source contribution points (max 20)
        if has_forks or any("contrib" in repo.name.lower() or "contribute" in repo.description.lower() for repo in candidate.github.repos):
            score += 20.0
            evidence.append("Open-source contributions or upstream project participation detected in GitHub profile.")
            
        # Star impact points (max 20)
        if max_stars >= 100:
            score += 20.0
            evidence.append(f"High-impact codebase shipped: max repository popularity reached {max_stars} stars.")
        elif max_stars >= 10:
            score += 10.0
            evidence.append(f"Public code validation: repository stars reached {max_stars} stars.")
    else:
        evidence.append("No public repository signals found to assess code community validation.")

    # 3. Technology stack diversity in side projects (20%)
    if candidate.side_projects:
        unique_techs = set()
        for p in candidate.side_projects:
            unique_techs.update(tech.lower() for tech in p.technologies)
            
        if len(unique_techs) >= 4:
            score += 20.0
            evidence.append(f"Polyglot builder: uses diverse technologies ({', '.join(list(unique_techs)[:5])}) in side projects.")
        elif len(unique_techs) >= 2:
            score += 10.0
            evidence.append(f"Demonstrated technology stack breadth across side projects.")
    else:
        evidence.append("No side project technology profiles available.")

    final_score = int(round(score))
    
    if final_score >= 75:
        rationale = "High creativity. Demonstrates unconventional software design choices, open-source presence, or highly validated public code bases."
    elif final_score >= 40:
        rationale = "Moderate creativity. Shows standard tool implementation with some evidence of technology breadth or repository validation."
    else:
        rationale = "Low creativity. Relies purely on template setups with no demonstrated non-standard architecture or public code impact."

    return DimensionScore(
        score=final_score,
        evidence=evidence,
        rationale=rationale,
    )
