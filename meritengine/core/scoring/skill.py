"""
meritengine/core/scoring/skill.py — Skill Scorer

Evaluates candidates on technical capability and demonstrated work
(GitHub profiles, coding assessments, and side projects) rather than pedigree.
"""

from meritengine.core.models import Candidate, DimensionScore, RoleSpec


def evaluate_skill(candidate: Candidate, role: RoleSpec) -> DimensionScore:
    """
    Evaluates a candidate's skill level (0-100) based on demonstrated evidence.

    Formula:
      skill_score = (0.4 * assessment_score) + (0.4 * github_score) + (0.2 * projects_score)
    """
    evidence: list[str] = []
    
    # 1. Assessment Component (40%)
    assessment_score = 0.0
    if candidate.assessment and candidate.assessment.submitted:
        raw_score = candidate.assessment.score or 0.0
        bonus = 0.0
        if candidate.assessment.is_working:
            bonus += 10.0
            evidence.append(
                f"Assessment solution is verified as working/functional (time taken: {candidate.assessment.time_taken_minutes or 'N/A'} mins)."
            )
        else:
            evidence.append("Assessment was submitted but failed working execution check.")

        if candidate.assessment.is_unconventional:
            bonus += 10.0
            evidence.append(
                f"Assessment used an unconventional/creative approach: {candidate.assessment.approach_description}"
            )
            
        assessment_score = min(raw_score + bonus, 100.0)
    else:
        evidence.append("No technical coding assessment or take-home challenge submitted.")

    # 2. GitHub Component (40%)
    github_score = 0.0
    if candidate.github:
        github = candidate.github
        repo_points = 0.0
        prod_repo_count = 0
        total_stars = 0
        total_forks = 0

        for repo in github.repos:
            # Production repos
            if repo.is_production:
                repo_points += 25.0
                prod_repo_count += 1
            # Stars & Forks
            if not repo.is_fork:
                total_stars += repo.stars
                total_forks += repo.forks
                # Commits in this repo
                repo_points += min(repo.total_commits / 5.0, 20.0)

        # Cap points from repo analysis
        github_score += min(repo_points, 65.0)

        # Star and fork bonuses
        github_score += min(total_stars / 10.0, 15.0)
        github_score += min(total_forks * 2.0, 10.0)

        # Commit activity last year
        if github.total_commits_last_year >= 800:
            github_score += 10.0
        elif github.total_commits_last_year >= 400:
            github_score += 5.0

        # Streak bonus
        github_score += min(github.contribution_streak_days / 10.0, 10.0)

        github_score = min(github_score, 100.0)

        evidence.append(
            f"GitHub profile ({github.username}) has {github.total_repos} repositories "
            f"with {github.total_commits_last_year} commits in the last year (streak: {github.contribution_streak_days} days)."
        )
        if prod_repo_count > 0:
            evidence.append(
                f"Identified {prod_repo_count} GitHub repositories marked as deployed production systems."
            )
    else:
        evidence.append("No public GitHub profile link provided or analyzed.")

    # 3. Side Projects Component (20%)
    projects_score = 0.0
    if candidate.side_projects:
        project_points = 0.0
        completed_count = 0
        matching_tech_count = 0
        
        role_skills = {s.name.lower() for s in role.required_skills}

        for project in candidate.side_projects:
            if project.status == "completed":
                project_points += 25.0
                completed_count += 1
            elif project.status == "in_progress":
                project_points += 15.0

            if project.url:
                project_points += 10.0

            # Match technologies
            for tech in project.technologies:
                if tech.lower() in role_skills:
                    project_points += 10.0
                    matching_tech_count += 1

        projects_score = min(project_points, 100.0)
        evidence.append(
            f"Submitted {len(candidate.side_projects)} side projects ({completed_count} completed), "
            f"matching {matching_tech_count} technologies required for the role."
        )
    else:
        evidence.append("No independent side projects or portfolio artifacts submitted.")

    # Calculate final weighted score
    final_score = int(round((0.4 * assessment_score) + (0.4 * github_score) + (0.2 * projects_score)))

    # Rationale generation
    if final_score >= 85:
        rationale = (
            "Exceptional demonstrated technical capability. Candidate has verified code production artifacts, "
            "excellent git activity, and a high-performing technical assessment."
        )
    elif final_score >= 60:
        rationale = (
            "Solid technical capability. Clean, functional code demonstrated via public repositories "
            "or technical assessment, aligning well with key role requirements."
        )
    elif final_score >= 30:
        rationale = (
            "Moderate technical capability. Some demonstrated work present, but lacks the depth of "
            "comprehensive public contributions or high assessment scoring."
        )
    else:
        rationale = (
            "Low verifiable technical capability. Lacks key public repositories, completed side projects, "
            "and working coding assessment submissions to substantiate technical claims."
        )

    return DimensionScore(
        score=final_score,
        evidence=evidence,
        rationale=rationale,
    )
