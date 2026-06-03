"""
meritengine/ingest/repo_analyzer.py — GitHub Repository and Profile Analyzer

Transforms raw repository lists and user stats into structured GitHub models.
"""

from datetime import date, datetime
from meritengine.core.models import GitHubProfile, GitHubRepo


def analyze_github_data(username: str, repos_raw: list[dict], profile_stats: dict) -> GitHubProfile:
    """
    Transforms dictionary-based GitHub responses into structured Pydantic objects,
    calculating aggregate parameters like streaks and production flags.
    """
    repos = []
    
    for r in repos_raw:
        last_commit = None
        if "last_commit_date" in r and r["last_commit_date"]:
            try:
                last_commit = date.fromisoformat(r["last_commit_date"])
            except ValueError:
                # If date format varies, fallback
                pass

        # Production flag heuristic
        name_lower = r.get("name", "").lower()
        desc_lower = r.get("description", "").lower()
        is_production = any(
            kw in name_lower or kw in desc_lower 
            for kw in ["production", "deployed", "api", "paystream", "live"]
        )

        repos.append(
            GitHubRepo(
                name=r.get("name", "unknown"),
                description=r.get("description", ""),
                stars=r.get("stars", 0),
                forks=r.get("forks", 0),
                total_commits=r.get("total_commits", 0),
                languages=r.get("languages", []),
                is_production=is_production,
                is_fork=r.get("is_fork", False),
                last_commit_date=last_commit,
            )
        )

    return GitHubProfile(
        username=username,
        total_repos=profile_stats.get("total_repos", len(repos)),
        total_commits_last_year=profile_stats.get("total_commits_last_year", 0),
        contribution_streak_days=profile_stats.get("contribution_streak_days", 0),
        repos=repos,
    )
