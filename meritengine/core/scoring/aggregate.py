"""
meritengine/core/scoring/aggregate.py — Score Aggregator and Anti-Bias Adjustments

Combines the 5 scoring dimensions, applies pedigree dampening, detects growth
trajectories, and outputs the final CandidateVerdict.
"""

from meritengine.core.models import (
    Candidate,
    CandidateVerdict,
    Dimensions,
    GrowthSignal,
    PedigreeAdjustment,
    RoleSpec,
    Verdict,
    CandidateType,
)


def aggregate_scores(
    candidate: Candidate,
    role: RoleSpec,
    dimensions: Dimensions,
) -> CandidateVerdict:
    """
    Aggregates individual dimension scores, applies pedigree/growth adjustments,
    and returns a complete CandidateVerdict.
    """
    # 1. Base Score (Weighted average)
    skill_val = dimensions.skill.score
    hunger_val = dimensions.hunger.score
    creativity_val = dimensions.creativity.score
    job_fit_val = dimensions.job_fit.score
    reliability_val = dimensions.reliability.score

    base_score = (
        0.30 * skill_val
        + 0.25 * hunger_val
        + 0.15 * creativity_val
        + 0.20 * job_fit_val
        + 0.10 * reliability_val
    )

    # 2. Pedigree Dampening
    pedigree_signals = []
    for edu in candidate.education:
        if edu.is_tier1:
            pedigree_signals.append(f"Education: {edu.institution} ({edu.degree})")
    for exp in candidate.work_experience:
        if exp.is_faang_or_brand:
            pedigree_signals.append(f"Work: {exp.company} ({exp.title})")

    pedigree_adj = PedigreeAdjustment()
    if pedigree_signals:
        # Dampening is proportional to the lack of demonstrated capabilities.
        # If demonstrated capabilities are high, discount is minimal.
        demonstrated_avg = (skill_val + hunger_val + creativity_val) / 3.0
        discount_factor = 0.3
        penalty = discount_factor * (100.0 - demonstrated_avg)
        net_change = -round(penalty, 1)

        pedigree_adj = PedigreeAdjustment(
            applied=True,
            signals_found=pedigree_signals,
            discount_factor=discount_factor,
            net_score_change=net_change,
            reason="Pedigree signals discounted per anti-bias policy to reward demonstrated capability.",
        )

    # 3. Growth Boost
    growth_detected = False
    growth_desc = ""
    multiplier = 1.0

    # Criteria for growth trajectory
    has_high_commits = candidate.github and candidate.github.total_commits_last_year >= 500
    has_unconventional_assessment = candidate.assessment and candidate.assessment.is_unconventional and candidate.assessment.is_working
    has_multiple_projects = len(candidate.side_projects) >= 2

    # If education is non-pedigree (or self-taught) and they have strong build signals
    is_non_pedigree = not any(edu.is_tier1 for edu in candidate.education)

    if (has_high_commits or has_multiple_projects or has_unconventional_assessment) and is_non_pedigree:
        growth_detected = True
        multiplier = 1.15
        growth_desc = "Steep growth trajectory: strong self-directed shipping signals combined with non-pedigree background."
    elif has_high_commits and has_unconventional_assessment:
        # For candidate with pedigree but still displaying exceptional growth
        growth_detected = True
        multiplier = 1.10
        growth_desc = "Strong growth trajectory: exceptional git contribution volume and unconventional assessment solutions."

    growth_sig = GrowthSignal(
        detected=growth_detected,
        description=growth_desc,
        multiplier_applied=multiplier,
    )

    # 4. Final Score Calculation
    adjusted_score = base_score + pedigree_adj.net_score_change
    final_score_val = max(0, min(100, int(round(adjusted_score * growth_sig.multiplier_applied))))

    # 5. Verdict Mapping
    if final_score_val >= 85:
        verdict: Verdict = "strong_hire"
    elif final_score_val >= 70:
        verdict: Verdict = "hire"
    elif final_score_val >= 55:
        verdict: Verdict = "lean_hire"
    elif final_score_val >= 40:
        verdict: Verdict = "hold"
    else:
        verdict: Verdict = "pass"

    # 6. Candidate Type Mapping
    if pedigree_adj.applied and growth_sig.detected:
        candidate_type: CandidateType = "both"
    elif growth_sig.detected:
        candidate_type: CandidateType = "promising"
    elif pedigree_adj.applied:
        candidate_type: CandidateType = "polished"
    else:
        candidate_type: CandidateType = "unclear"

    # 7. Red flags & Review Notes
    red_flags = []
    if not candidate.github and not candidate.side_projects:
        red_flags.append("Zero public code artifacts or side projects available for technical validation.")
    if candidate.assessment and not candidate.assessment.submitted:
        red_flags.append("Candidate did not submit the required take-home coding assessment.")

    # Confidence scoring based on available data profiles
    confidence = 1.0
    if not candidate.github:
        confidence -= 0.2
    if not candidate.assessment:
        confidence -= 0.2
    if not candidate.behavioral:
        confidence -= 0.1
    confidence = max(0.2, round(confidence, 2))

    return CandidateVerdict(
        candidate_id=candidate.id,
        evaluated_for_role=role.title,
        overall=final_score_val,
        verdict=verdict,
        candidate_type=candidate_type,
        dimensions=dimensions,
        pedigree_adjustment=pedigree_adj,
        growth_signal=growth_sig,
        red_flags=red_flags,
        human_review_notes=f"Evaluation completed with confidence score {confidence}.",
        confidence=confidence,
    )
