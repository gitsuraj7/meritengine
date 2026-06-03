"""
meritengine/ingest/resume_parser.py — Resume Parser

Parses resume text and structured profiles, flagging pedigree signals.
"""

import re
from meritengine.core.models import Candidate, Education, WorkExperience

TIER1_INSTITUTIONS = {
    "iit", "indian institute of technology", "mit", "stanford", 
    "harvard", "bits pilani", "bits", "iiit", "nit"
}

FAANG_BRANDS = {
    "google", "microsoft", "meta", "facebook", "amazon", 
    "netflix", "apple", "uber", "stripe", "netflix"
}


def parse_resume(raw_text: str, candidate_id: str, name: str = "Unknown") -> Candidate:
    """
    Rule-based resume parser that processes text to extract education,
    work experience, and pedigree markers.
    """
    education_entries = []
    work_entries = []

    # 1. Parse Education (Simple search)
    lines = raw_text.split("\n")
    for line in lines:
        line_lower = line.lower()
        # Look for degree signals
        if any(deg in line_lower for deg in ["b.tech", "btech", "degree", "diploma", "m.tech", "b.s.", "m.s.", "phd"]):
            is_tier1 = any(inst in line_lower for inst in TIER1_INSTITUTIONS)
            
            # Simple heuristic extraction
            degree = "B.Tech" if "b.tech" in line_lower or "btech" in line_lower else "Degree"
            if "diploma" in line_lower:
                degree = "Diploma"
            elif "phd" in line_lower:
                degree = "PhD"
                
            institution = "Unknown University"
            for inst in ["iit bombay", "iit delhi", "iit madras", "iit", "government polytechnic", "stanford", "mit"]:
                if inst in line_lower:
                    institution = inst.title()
                    break

            education_entries.append(
                Education(
                    institution=institution,
                    degree=degree,
                    field="Computer Science" if "science" in line_lower or "it" in line_lower else "General Engineering",
                    is_tier1=is_tier1,
                )
            )

    # 2. Parse Work Experience
    # Look for company names and duration indicators
    for line in lines:
        line_lower = line.lower()
        for company in FAANG_BRANDS | {"localpay solutions", "microsoft"}:
            if company in line_lower and any(kw in line_lower for kw in ["software engineer", "developer", "intern", "engineer"]):
                is_faang = company in FAANG_BRANDS
                
                # Check for experience duration signals (e.g. "3 years", "18 months")
                duration = 12
                dur_match = re.search(r"(\d+)\s*(year|month)", line_lower)
                if dur_match:
                    val = int(dur_match.group(1))
                    unit = dur_match.group(2)
                    duration = val * 12 if "year" in unit else val

                work_entries.append(
                    WorkExperience(
                        company=company.title(),
                        title="Software Engineer",
                        duration_months=duration,
                        description=line,
                        is_faang_or_brand=is_faang,
                    )
                )

    # Experience calculation
    total_exp = sum(w.duration_months for w in work_entries)

    # Try to extract skills
    skills_found = []
    for skill in ["python", "go", "postgresql", "redis", "docker", "system design", "java"]:
        if re.search(rf"\b{skill}\b", raw_text.lower()):
            skills_found.append(skill.title() if skill != "postgresql" else "PostgreSQL")

    return Candidate(
        id=candidate_id,
        name=name,
        skills_claimed=skills_found,
        education=education_entries,
        work_experience=work_entries,
        total_experience_months=total_exp,
        resume_text=raw_text,
    )
