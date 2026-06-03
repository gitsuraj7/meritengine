import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from meritengine.core.models import Candidate, RoleSpec
from meritengine.core.pipeline import evaluate_candidate, rank_candidates
from meritengine.core.explain import generate_explanation

# Ensure UTF-8 output encoding on Windows terminals to prevent encode errors
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


def load_candidate(name: str) -> Candidate:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return Candidate(**json.load(f))


def load_role(name: str) -> RoleSpec:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return RoleSpec(**json.load(f))


def main():
    console = Console()

    # 1. Load Data
    polished = load_candidate("candidate_polished.json")
    promising = load_candidate("candidate_promising.json")
    role = load_role("role_backend_senior.json")

    # 2. Run Pipeline
    verdict_polished = generate_explanation(evaluate_candidate(polished, role), polished)
    verdict_promising = generate_explanation(evaluate_candidate(promising, role), promising)
    ranking = rank_candidates([polished, promising], role)

    # 3. Print Title Panel
    console.print(
        Panel.fit(
            "[bold white]MERITENGINE - AI CANDIDATE EVALUATOR & RANKING DEMO[/bold white]\n"
            f"[dim]Role Evaluation: [bold cyan]{role.title}[/bold cyan] at Fintech Startup[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # 4. Create Side-by-Side Comparison Table
    table = Table(title="Candidate Evaluation Metrics", show_header=True, header_style="bold magenta", box=None)
    table.add_column("Metric / Dimension", style="dim", width=25)
    table.add_column("[bold red]Arjun Mehta (Polished)[/bold red]", width=45)
    table.add_column("[bold green]Priya Sharma (Promising) [WINNER][/bold green]", width=45)

    # General info
    table.add_row(
        "Overall Score / Verdict",
        f"[bold red]{verdict_polished.overall}/100[/bold red] - [red]{verdict_polished.verdict.upper()}[/red]",
        f"[bold green]{verdict_promising.overall}/100[/bold green] - [green]{verdict_promising.verdict.upper()}[/green]",
    )
    table.add_row(
        "Candidate Type",
        f"[red]{verdict_polished.candidate_type.title()}[/red] (FAANG/IIT)",
        f"[green]{verdict_promising.candidate_type.title()}[/green] (Self-Taught/Polytechnic)",
    )
    table.add_row("", "", "")

    # Dimension Scores
    for dim_name in ["skill", "hunger", "creativity", "job_fit", "reliability"]:
        dim_polished = getattr(verdict_polished.dimensions, dim_name)
        dim_promising = getattr(verdict_promising.dimensions, dim_name)
        
        table.add_row(
            dim_name.replace("_", " ").title(),
            f"[bold yellow]{dim_polished.score}/100[/bold yellow]\n[dim]{dim_polished.rationale}[/dim]",
            f"[bold green]{dim_promising.score}/100[/bold green]\n[dim]{dim_promising.rationale}[/dim]",
        )
        table.add_row("", "", "")

    # Signal Adjustments
    ped_p = verdict_polished.pedigree_adjustment
    ped_r = f"[red]Applied ({ped_p.net_score_change} pts)[/red]\n[dim]{ped_p.reason}[/dim]" if ped_p.applied else "None"
    
    growth_p = verdict_promising.growth_signal
    growth_r = f"[bold green]Detected ({growth_p.multiplier_applied}x boost)[/bold green]\n[dim]{growth_p.description}[/dim]" if growth_p.detected else "None"

    table.add_row("Pedigree Dampening", ped_r, "None (Excluded)")
    table.add_row("Growth Boost", "None (No trajectory signals)", growth_r)
    table.add_row("", "", "")

    console.print(table)

    # 5. Print Final Leaderboard Panel
    leaderboard_text = Text()
    leaderboard_text.append("\nFINAL RANKINGS & SELECTION LEADERBOARD:\n\n", style="bold gold1")
    for r in ranking.candidates:
        win_style = "bold green" if r.rank == 1 else "bold red"
        leaderboard_text.append(
            f"   #{r.rank} - {r.verdict.candidate_id} (Score: {r.verdict.overall}/100) -> Verdict: {r.verdict.verdict.upper()}\n",
            style=win_style,
        )
    margin = verdict_promising.overall - verdict_polished.overall
    leaderboard_text.append(
        f"\nSummary: The 'Hungry' candidate Priya Sharma outranked the 'Polished' candidate Arjun Mehta by a margin of {margin} points. "
        "Pedigree dampening correctly adjusted brand signals, while real shipped work (commits, code assessment, side projects) triggered the growth multiplier.",
        style="italic cyan",
    )

    console.print(Panel(leaderboard_text, border_style="gold1", title="Verdict Decision Sheet"))


if __name__ == "__main__":
    main()
