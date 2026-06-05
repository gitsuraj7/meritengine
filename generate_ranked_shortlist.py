import json
import csv
import sys
import os
from pathlib import Path

# Force offline embedding model fallback for fast processing
os.environ["MERITENGINE_OFFLINE"] = "1"

from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.pipeline import rank_candidates
from meritengine.core import db
from simulate import generate_candidate

# Ensure UTF-8 output encoding on Windows terminals to prevent encode errors
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("Initializing Database...")
    db.init_db()
    db.reset_db()

    print("Loading Job Spec Role and Candidate Fixtures...")
    fixtures_dir = Path("tests") / "fixtures"
    
    with open(fixtures_dir / "role_backend_senior.json", encoding="utf-8") as f:
        role = RoleSpec(**json.load(f))
        
    with open(fixtures_dir / "candidate_polished.json", encoding="utf-8") as f:
        polished = Candidate(**json.load(f))
        # Add logistics for compatibility
        polished.expected_ctc = 3400000
        polished.notice_period_days = 30
        
    with open(fixtures_dir / "candidate_promising.json", encoding="utf-8") as f:
        promising = Candidate(**json.load(f))
        # Add logistics for compatibility
        promising.expected_ctc = 2800000
        promising.notice_period_days = 15

    # Generate extra synthetic candidates to make a rich portfolio of 15 candidates
    candidates = [polished, promising]
    for i in range(1, 14):
        c = generate_candidate(100 + i)
        candidates.append(c)

    print(f"Evaluating and ranking {len(candidates)} candidates against the Senior Backend Engineer role...")
    ranking_result = rank_candidates(candidates, role)

    # Save verdicts to the actual SQLite DB
    verdicts = [rc.verdict for rc in ranking_result.candidates]
    db.save_batch_final_verdicts(verdicts)
    print("Verdicts successfully persisted in SQLite DB.")

    # Format shortlist for output
    shortlist_json = []
    for rc in ranking_result.candidates:
        c_obj = next(c for c in candidates if c.id == rc.verdict.candidate_id)
        
        # Clean the review notes to make it look professional
        notes_clean = rc.verdict.human_review_notes.replace("\n", " ").replace("  ", " ").strip()
        
        shortlist_json.append({
            "rank": rc.rank,
            "candidate_id": rc.verdict.candidate_id,
            "name": c_obj.name,
            "overall_score": rc.verdict.overall,
            "verdict": rc.verdict.verdict,
            "skills_claimed": c_obj.skills_claimed,
            "experience_months": c_obj.total_experience_months,
            "location": c_obj.location,
            "expected_ctc_lakhs": c_obj.expected_ctc / 100000 if c_obj.expected_ctc else None,
            "notice_period_days": c_obj.notice_period_days,
            "empathy_review_notes": notes_clean
        })

    # 1. Save JSON shortlist
    json_path = Path("ranked_shortlist.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(shortlist_json, f, indent=2)
    print(f"Ranked shortlist saved to: {json_path.resolve()}")

    # 2. Save CSV shortlist
    csv_path = Path("ranked_shortlist.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Candidate ID", "Name", "Overall Score", "Verdict", 
            "Skills Claimed", "Experience (Months)", "Location", "Expected CTC (Lakhs)", 
            "Notice Period (Days)", "Human Review Narrative"
        ])
        for s in shortlist_json:
            writer.writerow([
                s["rank"],
                s["candidate_id"],
                s["name"],
                s["overall_score"],
                s["verdict"],
                ", ".join(s["skills_claimed"]),
                s["experience_months"],
                s["location"],
                f"{s['expected_ctc_lakhs']:.1f}L" if s["expected_ctc_lakhs"] else "N/A",
                s["notice_period_days"],
                s["empathy_review_notes"]
            ])
    print(f"Ranked shortlist CSV saved to: {csv_path.resolve()}")

if __name__ == "__main__":
    main()
