"""
meritengine/ingest/role_parser.py — Job Description (JD) Parser

Parses raw Job Description text into structured RoleSpec models.
"""

import re
from meritengine.core.models import RoleSpec, SkillRequirement

KNOWN_SKILLS = ["python", "go", "postgresql", "redis", "docker", "system design", "rest apis", "java", "aws"]


def parse_role(raw_text: str, title: str = "Backend Engineer") -> RoleSpec:
    """
    Parses a job description to extract required/nice-to-have skills,
    experience constraints, and culture signals.
    """
    required_skills = []
    text_lower = raw_text.lower()

    # 1. Skill extraction
    for skill in KNOWN_SKILLS:
        if re.search(rf"\b{skill}\b", text_lower):
            # Check if it is a must_have or nice_to_have
            # Check text preceding the skill name
            idx = text_lower.find(skill)
            pre_window = text_lower[max(0, idx-40):idx]
            
            priority = "must_have"
            if any(w in pre_window for w in ["nice to have", "plus", "preferred", "optional", "desired"]):
                priority = "nice_to_have"
                
            # Formatting skill name
            skill_name = skill.title()
            if skill == "postgresql":
                skill_name = "PostgreSQL"
            elif skill == "rest apis":
                skill_name = "REST APIs"

            required_skills.append(
                SkillRequirement(
                    name=skill_name,
                    priority=priority,
                    min_years=2 if "senior" in title.lower() else 1
                )
            )

    # 2. Seniority & Experience Month Limits
    seniority = "mid"
    min_months = 12
    if "senior" in title.lower() or "senior" in text_lower:
        seniority = "senior"
        min_months = 24
    elif "junior" in title.lower() or "junior" in text_lower:
        seniority = "junior"
        min_months = 0
    elif "lead" in title.lower() or "lead" in text_lower:
        seniority = "lead"
        min_months = 48

    # 3. Culture Signals
    culture_signals = []
    for signal in ["ownership", "fast-paced", "ship-fast", "autonomous", "collaborative", "remote"]:
        if signal in text_lower:
            culture_signals.append(signal)

    return RoleSpec(
        title=title,
        required_skills=required_skills,
        seniority=seniority,
        min_experience_months=min_months,
        culture_signals=culture_signals,
        raw_jd_text=raw_text,
    )
