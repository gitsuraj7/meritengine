import sys
import time
import uuid
import random
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from meritengine.core.models import (
    Candidate,
    GitHubProfile,
    GitHubRepo,
    BehavioralSignals,
    RoleSpec,
    SkillRequirement,
    SideProject,
    WorkExperience
)
from meritengine.core.router import global_router

# Ensure stdout encodes to utf-8 properly for rich
sys.stdout.reconfigure(encoding='utf-8')

# Mock semantic embeddings for massive simulation
import meritengine.core.scoring.job_fit as job_fit_module
job_fit_module.get_embedding_model = lambda: "fallback"

console = Console()

role = RoleSpec(
    title="Staff Backend Engineer (Distributed Systems)",
    department="Engineering",
    seniority="staff",
    required_skills=[
        SkillRequirement(name="Python", priority="must_have"),
        SkillRequirement(name="Go", priority="must_have"),
        SkillRequirement(name="PostgreSQL", priority="must_have"),
        SkillRequirement(name="Kafka", priority="nice_to_have"),
        SkillRequirement(name="Redis", priority="nice_to_have")
    ],
    domain="fintech",
    environment="scaleup",
    min_experience_months=72,
    budget_max_ctc=50.0,
    max_notice_period_days=45,
    location="Bangalore",
    remote_ok=True,
    direct_seats=10,
    waitlist_seats=5,
    backup_seats=15
)

def generate_candidate_batch(batch_size: int) -> list[Candidate]:
    candidates = []
    for _ in range(batch_size):
        cid = str(uuid.uuid4())
        
        # The semantic mock must return scores drawn from a seeded random distribution per candidate
        random.seed(cid)
        semantic_score = random.uniform(0.3, 0.95)
        
        missing_critical = random.random() < 0.05
        name = "" if missing_critical else f"Candidate {cid[:8]}"
        email = "" if missing_critical else f"cand_{cid[:8]}@example.com"
        resume_text = "" if missing_critical else "Staff Engineer with Python and Go experience. " * 3
        
        current_ctc = random.choice([30.0, 40.0, 45.0, 55.0, 60.0])
        notice = random.choice([30, 45, 60, 90])
        location = random.choice(["Bangalore", "Pune", "Remote"])
        will_relocate = random.random() < 0.5
        
        is_stream_a = random.random() < 0.15 
        repos = []
        side_projects = []
        if is_stream_a:
            repos = [GitHubRepo(name=f"repo{i}", stars=10) for i in range(2)]
            side_projects = [SideProject(name="demo", status="completed", technologies=["Python", "Go"])]
            
        resp_rate = random.uniform(0.7, 1.0)
        avg_time = random.uniform(2, 48)
        behavioral = BehavioralSignals(response_rate=resp_rate, avg_response_time_hours=avg_time)
        
        work_exp = [WorkExperience(company="Acme", title="Engineer", duration_months=80)]
        
        c = Candidate(
            id=cid,
            name=name,
            email=email,
            resume_text=resume_text,
            bio="Software engineer.",
            current_ctc=current_ctc,
            notice_period_days=notice,
            location=location,
            willing_to_relocate=will_relocate,
            github=GitHubProfile(username="test", repos=repos) if repos else None,
            side_projects=side_projects,
            behavioral=behavioral,
            work_experience=work_exp,
            skills_claimed=["Python", "Go"]
        )
        c._semantic_fit_score = semantic_score
        candidates.append(c)
        
        random.seed()
        
    return candidates

def run_simulation():
    ROUNDS = 100
    BATCH_SIZE = 64000
    
    total_processed = 0
    total_fast_rejected = 0
    total_survived_l1 = 0
    total_stz_promotions = 0
    direct_seats_filled_count = 0
    total_time_ms = 0
    
    console.print(Panel(f"[bold cyan]Starting MeritEngine Massive Scale Simulation[/bold cyan]\n"
                        f"Target: {ROUNDS} rounds x {BATCH_SIZE:,} candidates = {ROUNDS * BATCH_SIZE:,} total.\n"
                        f"Role: {role.title} | Budget: {role.budget_max_ctc} LPA | Notice: {role.max_notice_period_days} days\n"
                        f"Seats: {role.direct_seats} direct, {role.waitlist_seats} waitlist, {role.backup_seats} backup", 
                        title="Configuration"))
    
    for r in track(range(1, ROUNDS + 1), description="Processing Rounds..."):
        start_time = time.time()
        global_router.reset()
        
        candidates = generate_candidate_batch(BATCH_SIZE)
        global_router.run_batch(candidates, role)
        
        # Approve all supervisor candidates
        for c, _ in list(global_router.supervisor_queue):
            global_router.resolve_supervisor_decision(c.id, True)
            
        result = global_router.finalize_battle(role)
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        total_time_ms += elapsed_ms
        total_processed += BATCH_SIZE
        
        # Gather metrics
        round_fast_rejected = sum(1 for v in global_router.final_verdicts if v.overall == 0 and ("Failed Stage 1" in v.red_flags[0] or "Failed Stage 2" in v.red_flags[0]))
        total_fast_rejected += round_fast_rejected
        
        total_stz_promotions += global_router.stz_promotions_count
        total_survived_l1 += global_router.l1_promotions_count
        
        direct_hires = sum(1 for c in result.candidates if c.verdict.verdict == "strong_hire")
        if direct_hires == role.direct_seats:
            direct_seats_filled_count += 1

    avg_time_ms = total_time_ms / ROUNDS
    
    summary = {
        "total_processed": total_processed,
        "total_fast_rejected": total_fast_rejected,
        "total_survived_l1": total_survived_l1,
        "total_stz_promotions": total_stz_promotions,
        "direct_seats_filled_count": direct_seats_filled_count,
        "average_round_processing_time_ms": round(avg_time_ms, 2)
    }
    
    with open("simulation_results.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    table = Table(title="Final Simulation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Total Candidates Processed", f"{total_processed:,}")
    table.add_row("Total Fast-Rejected (Fatal Faults/Triage)", f"{total_fast_rejected:,}")
    table.add_row("Total Survived to Level 1", f"{total_survived_l1:,}")
    table.add_row("Total STZ Promotions", f"{total_stz_promotions:,}")
    table.add_row("Cumulative Seat Fill Rate (Direct)", f"{direct_seats_filled_count}/{ROUNDS} rounds")
    table.add_row("Average Round Processing Time", f"{avg_time_ms:,.2f} ms")
    
    console.print(table)
    console.print("[green]Simulation complete! Proof saved to simulation_results.json[/green]")

if __name__ == "__main__":
    run_simulation()
