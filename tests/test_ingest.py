"""
tests/test_ingest.py — Unit tests for resume_parser, role_parser, and repo_analyzer.
"""

from meritengine.ingest.resume_parser import parse_resume
from meritengine.ingest.role_parser import parse_role
from meritengine.ingest.repo_analyzer import analyze_github_data


def test_resume_parser_polished():
    raw_resume = (
        "Arjun Mehta\n"
        "IIT Bombay B.Tech Computer Science 2020\n"
        "Google Software Engineer for 3 years (36 months)\n"
        "Microsoft SDE Intern 3 months"
    )
    candidate = parse_resume(raw_resume, "test-polished", "Arjun Mehta")

    assert candidate.id == "test-polished"
    assert candidate.name == "Arjun Mehta"
    assert len(candidate.education) == 1
    assert candidate.education[0].is_tier1 is True
    assert candidate.education[0].institution == "Iit Bombay"
    
    assert len(candidate.work_experience) == 2
    assert candidate.work_experience[0].is_faang_or_brand is True
    assert candidate.work_experience[0].company == "Google"
    assert candidate.work_experience[0].duration_months == 36


def test_resume_parser_promising():
    raw_resume = (
        "Priya Sharma\n"
        "Diploma from Government Polytechnic, Lucknow\n"
        "Backend Developer at LocalPay Solutions 18 months\n"
        "Skills: Python, Go, PostgreSQL, Redis, Docker"
    )
    candidate = parse_resume(raw_resume, "test-promising", "Priya Sharma")

    assert candidate.id == "test-promising"
    assert candidate.education[0].is_tier1 is False
    assert candidate.education[0].institution == "Government Polytechnic"
    assert candidate.work_experience[0].company == "Localpay Solutions"
    assert candidate.work_experience[0].is_faang_or_brand is False
    assert candidate.work_experience[0].duration_months == 18
    assert "Python" in candidate.skills_claimed
    assert "Go" in candidate.skills_claimed


def test_role_parser():
    jd_text = (
        "Looking for a Senior Backend Engineer who owns systems end-to-end.\n"
        "Required skills: Python, PostgreSQL. Nice to have: Go, Redis.\n"
        "We operate in a fast-paced environment and value high ownership."
    )
    role = parse_role(jd_text, "Senior Backend Engineer")

    assert role.title == "Senior Backend Engineer"
    assert role.seniority == "senior"
    assert role.min_experience_months == 24
    
    must_haves = [s for s in role.required_skills if s.priority == "must_have"]
    nice_to_haves = [s for s in role.required_skills if s.priority == "nice_to_have"]
    
    assert len(must_haves) == 2
    assert len(nice_to_haves) == 2
    assert "ownership" in role.culture_signals
    assert "fast-paced" in role.culture_signals


def test_repo_analyzer():
    repos_raw = [
        {
            "name": "paystream-api",
            "description": "Production payment processing API",
            "stars": 34,
            "forks": 8,
            "total_commits": 312,
            "languages": ["Python", "Go"],
            "is_fork": False,
            "last_commit_date": "2026-05-28",
        }
    ]
    stats = {
        "total_repos": 1,
        "total_commits_last_year": 847,
        "contribution_streak_days": 94,
    }
    
    profile = analyze_github_data("priya-builds", repos_raw, stats)

    assert profile.username == "priya-builds"
    assert profile.total_commits_last_year == 847
    assert len(profile.repos) == 1
    assert profile.repos[0].is_production is True
    assert profile.repos[0].stars == 34
