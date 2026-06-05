"""
meritengine/core/scoring/job_fit.py — Job Fit Scorer

Evaluates candidate fit against the RoleSpec utilizing semantic text similarity
(via SentenceTransformers) and cultural alignment keywords.
"""

import re
import math
import numpy as np
from meritengine.core.models import Candidate, DimensionScore, RoleSpec

# Lazy-loaded model cache
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        import os
        if os.environ.get("MERITENGINE_OFFLINE") == "1":
            _model = "fallback"
            return _model
        try:
            from sentence_transformers import SentenceTransformer
            # Use the tiny, highly efficient 22MB model
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            _model = "fallback"
    return _model


def compute_semantic_similarity(text1: str, text2: str) -> float:
    """Computes cosine similarity between two texts using SentenceTransformer or TF-IDF fallback."""
    if not text1 or not text2:
        return 0.0
        
    model = get_embedding_model()
    if model == "fallback":
        # Rule-based fallback: word intersection ratio
        w1 = set(re.findall(r'\w+', text1.lower()))
        w2 = set(re.findall(r'\w+', text2.lower()))
        if not w1 or not w2:
            return 0.0
        return len(w1.intersection(w2)) / math.sqrt(len(w1) * len(w2))

    try:
        embeddings = model.encode([text1, text2])
        dot = np.dot(embeddings[0], embeddings[1])
        norm1 = np.linalg.norm(embeddings[0])
        norm2 = np.linalg.norm(embeddings[1])
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))
    except Exception:
        return 0.5  # Neutral fallback on error


def evaluate_job_fit(candidate: Candidate, role: RoleSpec) -> DimensionScore:
    """
    Scores job fit (0-100) combining experience alignment, skill coverage, 
    culture match, and semantic vector similarity.
    """
    evidence: list[str] = []
    score = 0.0

    # 1. Experience Years Alignment (20%)
    min_exp = role.min_experience_months
    candidate_exp = candidate.total_experience_months
    
    if candidate_exp >= min_exp:
        score += 20.0
        evidence.append(
            f"Experience duration match: candidate has {candidate_exp} months of experience (min: {min_exp})."
        )
    else:
        ratio = candidate_exp / max(1.0, float(min_exp))
        points = ratio * 12.0
        score += points
        evidence.append(
            f"Experience gap: candidate has {candidate_exp} months of experience (min requested: {min_exp})."
        )

    # 2. Skill Requirements Match (30%)
    proven_skills = set(s.lower() for s in candidate.skills_claimed)
    if candidate.github:
        for repo in candidate.github.repos:
            proven_skills.update(l.lower() for l in repo.languages)
    for p in candidate.side_projects:
        proven_skills.update(t.lower() for t in p.technologies)

    must_haves = [s for s in role.required_skills if s.priority == "must_have"]
    nice_to_haves = [s for s in role.required_skills if s.priority == "nice_to_have"]

    must_have_matches = sum(1 for s in must_haves if s.name.lower() in proven_skills)
    nice_to_have_matches = sum(1 for s in nice_to_haves if s.name.lower() in proven_skills)

    if must_haves:
        score += (must_have_matches / len(must_haves)) * 20.0
        evidence.append(f"Matched {must_have_matches} of {len(must_haves)} must-have skills.")
    else:
        score += 20.0

    if nice_to_haves:
        score += (nice_to_have_matches / len(nice_to_haves)) * 10.0
        evidence.append(f"Matched {nice_to_have_matches} of {len(nice_to_haves)} nice-to-have skills.")
    else:
        score += 10.0

    # 3. Domain & Culture Alignment (15%)
    candidate_text = (
        candidate.bio + " " +
        candidate.resume_text + " " +
        " ".join(exp.description for exp in candidate.work_experience)
    ).lower()

    if role.domain.lower() and role.domain.lower() in candidate_text:
        score += 5.0
        evidence.append(f"Domain match detected: Context found in {role.domain}.")

    culture_matches = sum(1 for sig in role.culture_signals if sig.lower() in candidate_text)
    if role.culture_signals:
        score += min((culture_matches / len(role.culture_signals)) * 10.0, 10.0)
        if culture_matches > 0:
            evidence.append(f"Culture alignment: matched {culture_matches} working style signals.")
    else:
        score += 10.0

    # 4. Semantic Similarity Model Analysis (35%)
    # Combine candidate's experience description + bio
    candidate_profile_text = f"{candidate.bio} {candidate.resume_text} " + " ".join(
        exp.description for exp in candidate.work_experience
    )
    
    # Combine role spec details
    role_profile_text = f"{role.title} {role.domain} " + " ".join(role.key_responsibilities) + f" {role.raw_jd_text}"

    if hasattr(candidate, "_semantic_fit_score"):
        semantic_sim = candidate._semantic_fit_score
    else:
        semantic_sim = compute_semantic_similarity(candidate_profile_text, role_profile_text)

    semantic_points = semantic_sim * 35.0
    score += semantic_points
    evidence.append(
        f"Semantic profile alignment: neural text match score is {semantic_sim * 100:.1f}%."
    )

    # 5. Growth Mindset/Human Factor Check (Bonus +5%)
    # Reward human-centric attributes in text: growth, learnability, ownership
    growth_keywords = ["learn", "adapt", "experiment", "tackle", "solved", "ownership", "shipped", "built"]
    growth_hits = sum(1 for kw in growth_keywords if kw in candidate_text)
    if growth_hits >= 3:
        score += 5.0
        evidence.append("Positive signals: candidate's written experience shows high learnability and shipping ownership.")

    final_score = int(round(min(score, 100.0)))
    
    if final_score >= 80:
        rationale = "Exceptional job fit. Strong semantic alignment, key tech skills, and high growth learnability traits."
    elif final_score >= 50:
        rationale = "Moderate job fit. Meets core skill demands but has experience alignment gaps or lacks domain specificity."
    else:
        rationale = "Low job fit. Candidate skillset and experience duration diverge significantly from role requirements."

    return DimensionScore(
        score=final_score,
        evidence=evidence,
        rationale=rationale,
    )
