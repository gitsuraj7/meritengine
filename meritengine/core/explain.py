"""
meritengine/core/explain.py — Explanation Generator

Enriches candidate verdicts with detailed, structured, human-readable
markdown justifications detailing the evaluation dimensions and adjustments.
"""

from meritengine.core.models import Candidate, CandidateVerdict


def generate_explanation(verdict: CandidateVerdict, candidate: Candidate) -> CandidateVerdict:
    """
    Enriches the CandidateVerdict with detailed markdown-formatted human_review_notes
    justifying the overall score, verdict, dimensions, and anti-bias adjustments.
    """
    sections = []
    
    # 1. Summary Header
    status_emoji = {
        "strong_hire": "🟢 [STRONG HIRE]",
        "hire": "🟢 [HIRE]",
        "lean_hire": "🟡 [LEAN HIRE]",
        "hold": "🟠 [HOLD]",
        "pass": "🔴 [PASS]"
    }.get(verdict.verdict, "⚪ [HOLD]")

    sections.append(
        f"### {status_emoji} {candidate.name} (Score: {verdict.overall}/100)\n"
        f"**Candidate Type:** {verdict.candidate_type.title()}\n"
        f"**Confidence Level:** {verdict.confidence * 100:.0f}%\n"
    )

    # 2. Dimensions Breakdown
    sections.append("#### 📊 Dimension Breakdown")
    for name in ["skill", "hunger", "creativity", "job_fit", "reliability"]:
        dim_score = getattr(verdict.dimensions, name)
        # Format name
        title = name.replace("_", " ").title()
        sections.append(
            f"- **{title} ({dim_score.score}/100):** {dim_score.rationale}\n"
            f"  *Evidence:* {'; '.join(dim_score.evidence) if dim_score.evidence else 'None'}"
        )
    sections.append("")

    # 3. Adjustments Section
    sections.append("#### ⚖️ Signal Adjustments")
    if verdict.pedigree_adjustment.applied:
        sections.append(
            f"- **Pedigree Dampening Applied (Discount: {verdict.pedigree_adjustment.discount_factor}):**\n"
            f"  *Signals Found:* {', '.join(verdict.pedigree_adjustment.signals_found)}\n"
            f"  *Score Impact:* {verdict.pedigree_adjustment.net_score_change} points. {verdict.pedigree_adjustment.reason}"
        )
    else:
        sections.append("- No pedigree signals discounted.")

    if verdict.growth_signal.detected:
        sections.append(
            f"- **Growth Boost Applied (Multiplier: {verdict.growth_signal.multiplier_applied}x):**\n"
            f"  *Details:* {verdict.growth_signal.description}"
        )
    else:
        sections.append("- No growth trajectory boost applied.")
    sections.append("")

    # 4. Red Flags
    if verdict.red_flags:
        sections.append("#### ⚠️ Red Flags / Risk Factors")
        for flag in verdict.red_flags:
            sections.append(f"- {flag}")
    else:
        sections.append("#### ✅ No Red Flags Detected")

    # Update verdict and return
    verdict.human_review_notes = "\n".join(sections)
    return verdict
