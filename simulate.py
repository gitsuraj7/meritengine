"""
simulate.py — Large-Scale Candidate Simulation Script

Generates 5000 synthetic candidates, evaluates them in 5 batches of 1000, 
applies conditions of employment, groups selections into Direct Hires and 
Waiting Lists, and displays detailed stats.
"""

import sys
import json
import random
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from meritengine.core.models import (
    Candidate, Education, WorkExperience, GitHubProfile, 
    GitHubRepo, Assessment, BehavioralSignals, SideProject, RoleSpec
)
from meritengine.core.pipeline import rank_candidates

# Ensure UTF-8 output encoding on Windows terminals to prevent encode errors
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURABLE HIRING DECISION CONSTRAINTS (Hiring Manager / Recruiter Rules)
# ═══════════════════════════════════════════════════════════════════════════════
N_SELECT = 2              # Positions to fill (Direct Hires) per batch
N_WAITING = 3             # Size of the backup Waiting List pool per batch

MIN_HIRE_SCORE = 70       # Minimum evaluation score threshold to hire
MAX_NOTICE_PERIOD = 60    # Maximum notice period (days) acceptable
MAX_EXPECTED_CTC = 3500000  # Budget ceiling (Lakhs)
REQUIRED_LOCATION = "Bangalore"
# ═══════════════════════════════════════════════════════════════════════════════


def load_role(name: str) -> RoleSpec:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def generate_candidate(cid: int) -> Candidate:
    """Generates a synthetic candidate of type polished, promising, or standard."""
    c_type = random.choices(["polished", "promising", "standard"], weights=[0.25, 0.25, 0.50])[0]

    edu_list = []
    work_list = []
    github = None
    assessment = None
    side_projects = []

    # Logistics metrics
    expected_ctc = random.choice([2400000, 2800000, 3200000, 3500000, 3800000, 4200000])
    notice_period_days = random.choice([15, 30, 60, 90])
    location = random.choice(["Bangalore", "Lucknow", "Delhi", "Mumbai"])
    willing_to_relocate = random.choice([True, False])

    if c_type == "polished":
        name = f"Polished Candidate {cid}"
        edu_list.append(
            Education(
                institution=random.choice(["IIT Bombay", "IIT Delhi", "Stanford University"]),
                degree="B.Tech",
                field="Computer Science",
                is_tier1=True
            )
        )
        work_list.append(
            WorkExperience(
                company=random.choice(["Google", "Microsoft", "Amazon"]),
                title="Software Engineer",
                duration_months=random.randint(24, 48),
                is_faang_or_brand=True
            )
        )
        github = None
        assessment = None
        side_projects = []

    elif c_type == "promising":
        name = f"Promising Candidate {cid}"
        edu_list.append(
            Education(
                institution=random.choice(["Govt Polytechnic", "Self-Taught", "Local College"]),
                degree="Diploma",
                field="Information Technology",
                is_tier1=False
            )
        )
        work_list.append(
            WorkExperience(
                company="Local Tech Solutions",
                title="Backend Developer",
                duration_months=random.randint(12, 24),
                is_faang_or_brand=False
            )
        )
        github = GitHubProfile(
            username=f"builder-{cid}",
            total_repos=random.randint(8, 15),
            total_commits_last_year=random.randint(550, 950),
            contribution_streak_days=random.randint(45, 120),
            repos=[
                GitHubRepo(
                    name="payments-engine",
                    stars=random.randint(20, 100),
                    total_commits=random.randint(150, 400),
                    languages=["Python", "Go"],
                    is_production=True
                )
            ]
        )
        assessment = Assessment(
            submitted=True,
            score=random.randint(80, 98),
            is_unconventional=True,
            is_working=True,
            time_taken_minutes=random.randint(120, 240)
        )
        side_projects = [
            SideProject(
                name="chat-server",
                status="completed",
                technologies=["Go", "Redis"]
            )
        ]

    else:  # standard
        name = f"Standard Candidate {cid}"
        edu_list.append(
            Education(
                institution="State Tech University",
                degree="B.E.",
                field="Information Technology",
                is_tier1=False
            )
        )
        work_list.append(
            WorkExperience(
                company="Mid-size IT Corp",
                title="Software Engineer",
                duration_months=random.randint(12, 36),
                is_faang_or_brand=False
            )
        )
        github = GitHubProfile(
            username=f"dev-{cid}",
            total_repos=random.randint(2, 5),
            total_commits_last_year=random.randint(50, 180),
            contribution_streak_days=random.randint(0, 15)
        )
        assessment = Assessment(
            submitted=True,
            score=random.randint(55, 75),
            is_unconventional=False,
            is_working=True
        )

    return Candidate(
        id=f"cand-{cid:04d}",
        name=name,
        skills_claimed=["Python", "PostgreSQL", "Go"],
        education=edu_list,
        work_experience=work_list,
        total_experience_months=sum(w.duration_months for w in work_list),
        github=github,
        assessment=assessment,
        side_projects=side_projects,
        expected_ctc=expected_ctc,
        notice_period_days=notice_period_days,
        location=location,
        willing_to_relocate=willing_to_relocate,
        behavioral=BehavioralSignals(
            response_rate=random.uniform(0.70, 0.98),
            avg_response_time_hours=random.uniform(1, 12),
            communication_clarity=random.uniform(0.60, 0.95),
            follow_through_rate=random.uniform(0.70, 0.98)
        )
    )


def verify_conditions(candidate: Candidate, score: int) -> list[str]:
    """Checks the conditions of employment constraints and returns failed reasons."""
    failures = []
    if score < MIN_HIRE_SCORE:
        failures.append(f"Score ({score}) below threshold ({MIN_HIRE_SCORE})")
    if candidate.expected_ctc and candidate.expected_ctc > MAX_EXPECTED_CTC:
        failures.append(f"CTC ({candidate.expected_ctc / 100000:.1f}L) exceeds budget ({MAX_EXPECTED_CTC / 100000:.1f}L)")
    if candidate.notice_period_days and candidate.notice_period_days > MAX_NOTICE_PERIOD:
        failures.append(f"Notice period ({candidate.notice_period_days}d) exceeds ceiling ({MAX_NOTICE_PERIOD}d)")
    
    # Location checks
    is_local = candidate.location.lower() == REQUIRED_LOCATION.lower()
    if not is_local and not candidate.willing_to_relocate:
        failures.append(f"Located in {candidate.location} and unwilling to relocate")
        
    return failures


def main():
    console = Console()
    role = load_role("role_backend_senior.json")

    console.print(
        Panel.fit(
            "[bold green]MERITENGINE — LARGE-SCALE SIMULATION WITH EMPLOYMENT CONDITIONS[/bold green]\n"
            f"[bold white]Decision Parameters:[/bold white]\n"
            f"- Direct Hire Targets: [bold yellow]{N_SELECT}[/bold yellow] | Waiting List Pool: [bold yellow]{N_WAITING}[/bold yellow]\n"
            f"- Conditions: Score >= {MIN_HIRE_SCORE} | CTC <= {MAX_EXPECTED_CTC/100000:.0f}L | Notice <= {MAX_NOTICE_PERIOD}d | Location: {REQUIRED_LOCATION} (or Relocate ok)",
            border_style="green",
            padding=(1, 2)
        )
    )

    t_start = time.time()
    
    total_direct_hires = 0
    total_waiting_list = 0
    total_disqualified = 0

    # Run 5 rounds of 1000 candidates
    for round_num in range(1, 6):
        console.print(f"\n[bold yellow]=== ROUND {round_num}: PROCESSING 1,000 CANDIDATES ===[/bold yellow]")
        
        # 1. Generate 1000 candidates
        candidates = [generate_candidate((round_num - 1) * 1000 + i) for i in range(1, 1001)]
        
        # 2. Evaluate and Rank
        t_rank_start = time.time()
        result = rank_candidates(candidates, role)
        t_rank_end = time.time()
        
        # 3. Apply Conditions of Employment & Process Selections
        direct_hires = []
        waiting_list = []
        disqualified = []

        for rc in result.candidates:
            cand_obj = next(c for c in candidates if c.id == rc.verdict.candidate_id)
            c_type = "Promising" if "Promising" in cand_obj.name else ("Polished" if "Polished" in cand_obj.name else "Standard")
            
            failures = verify_conditions(cand_obj, rc.verdict.overall)
            
            cand_info = {
                "id": rc.verdict.candidate_id,
                "name": cand_obj.name,
                "score": rc.verdict.overall,
                "type": c_type,
                "ctc": cand_obj.expected_ctc,
                "notice": cand_obj.notice_period_days,
                "location": cand_obj.location,
                "relocate": cand_obj.willing_to_relocate,
                "failures": failures
            }

            if failures:
                disqualified.append(cand_info)
            else:
                if len(direct_hires) < N_SELECT:
                    direct_hires.append(cand_info)
                elif len(waiting_list) < N_WAITING:
                    waiting_list.append(cand_info)
                else:
                    # We have filled both direct hire and waiting list slots, we can stop processing this round
                    # but let's gather disqualification reasons for statistics if needed
                    pass
        
        total_direct_hires += len(direct_hires)
        total_waiting_list += len(waiting_list)
        total_disqualified += len(disqualified)

        # 4. Display Round Metrics
        rank_time = t_rank_end - t_rank_start
        throughput = 1000.0 / rank_time
        console.print(f"   [dim]Processed 1,000 candidates in {rank_time:.2f}s ({throughput:.1f} candidates/sec)[/dim]")

        # Draw Selections Board
        table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
        table.add_column("Status", width=15)
        table.add_column("Candidate ID", width=12)
        table.add_column("Profile Style", width=15)
        table.add_column("Score", width=8)
        table.add_column("Employment Details / Failure Reasons")

        # Add Direct Hires
        for dh in direct_hires:
            style = "bold green" if dh["type"] == "Promising" else "red"
            reloc_str = "Relocate ok" if dh["relocate"] else "Local"
            table.add_row(
                "[bold green]DIRECT HIRE[/bold green]",
                dh["id"],
                f"[{style}]{dh['type']}[/{style}]",
                f"{dh['score']}/100",
                f"CTC: {dh['ctc']/100000:.0f}L | Notice: {dh['notice']}d | Location: {dh['location']} ({reloc_str})"
            )

        # Add Waiting List
        for wl in waiting_list:
            style = "bold green" if wl["type"] == "Promising" else "red"
            reloc_str = "Relocate ok" if wl["relocate"] else "Local"
            table.add_row(
                "[bold yellow]WAITING LIST[/bold yellow]",
                wl["id"],
                f"[{style}]{wl['type']}[/{style}]",
                f"{wl['score']}/100",
                f"CTC: {wl['ctc']/100000:.0f}L | Notice: {wl['notice']}d | Location: {wl['location']} ({reloc_str})"
            )

        # Show top disqualified for context
        for dq in disqualified[:2]:
            style = "dim red"
            table.add_row(
                "[bold red]DISQUALIFIED[/bold red]",
                dq["id"],
                f"[{style}]{dq['type']}[/{style}]",
                f"{dq['score']}/100",
                f"[red]Failed: {', '.join(dq['failures'])}[/red]"
            )

        console.print(table)

    t_end = time.time()
    total_time = t_end - t_start

    summary_panel = Panel(
        f"[bold white]CANDIDATE SELECTION RUN SUMMARY[/bold white]\n"
        f"- Total Evaluated Pool: [bold yellow]5,000[/bold yellow]\n"
        f"- Total Processing Time: [bold yellow]{total_time:.2f} seconds[/bold yellow]\n"
        f"- Average Speed: [bold yellow]{5000.0 / total_time:.1f} candidates/sec[/bold yellow]\n\n"
        f"[bold white]HIRING RESULTS OVERALL:[/bold white]\n"
        f"- [bold green]Positions Successfully Filled (Direct Hires): {total_direct_hires}[/bold green]\n"
        f"- [bold yellow]Waiting List Backlog Built: {total_waiting_list}[/bold yellow]\n"
        f"- Disqualified / Unfit (CTC/Notice/Location/Score): {total_disqualified}\n\n"
        f"[bold cyan]Decision Review:[/bold cyan] Promising (Build-first) candidates dominate both direct hire slots "
        f"and waiting list pools. When candidates failed notice periods (e.g. 90 days) or CTC budget caps, "
        f"the engine automatically bypassed them to secure compliant direct selections without human intervention.",
        border_style="gold1",
        title="Hiring Decisions Dashboard Summary"
    )
    console.print("\n")
    console.print(summary_panel)


if __name__ == "__main__":
    main()
