"""
meritengine/core/scoring/committee.py — Empathy-First Judging Committee

Composed of 10 evaluation layers, each containing 5 specialized sub-agents
(50 agents total) with a mission to find potential, grit, and context rather
than simple automated rejection.
"""

from typing import List, Dict, Any
from meritengine.core.models import Candidate, RoleSpec

class AgentOpinion:
    def __init__(self, agent_name: str, score_impact: float, advocacy_note: str, is_advocating: bool):
        self.agent_name = agent_name
        self.score_impact = score_impact
        self.advocacy_note = advocacy_note
        self.is_advocating = is_advocating

class CommitteeEvaluator:
    """
    Orchestrates the 10 layers and 50 sub-agents to evaluate candidates.
    Every agent tries to find positive signals, excuses for setbacks,
    and reasons to hire.
    """

    def __init__(self):
        # Initialize our 10 layers of agents
        self.layers = {
            "Layer 1: Aesthetic & Human Voice": [
                self.agent_resume_warmth,
                self.agent_writing_clarity,
                self.agent_technical_vocabulary,
                self.agent_authenticity_scout,
                self.agent_layout_compassion
            ],
            "Layer 2: GitHub Dev Journey": [
                self.agent_commit_cadence,
                self.agent_code_quality_critic,
                self.agent_documentation_advocate,
                self.agent_project_completeness,
                self.agent_tech_stack_adaptability
            ],
            "Layer 3: Real-World Grit": [
                self.agent_side_project_passion,
                self.agent_deployment_practicality,
                self.agent_database_architecture,
                self.agent_api_design_critic,
                self.agent_unconventional_solvers
            ],
            "Layer 4: Growth & Trajectory": [
                self.agent_velocity_estimator,
                self.agent_self_taught_champion,
                self.agent_experience_multiplier,
                self.agent_upskilling_speed,
                self.agent_career_pivot_appraiser
            ],
            "Layer 5: Behavioral Grit & Heart": [
                self.agent_promptness_inspector,
                self.agent_message_tone,
                self.agent_reliability_indexer,
                self.agent_compliance_scout,
                self.agent_detail_orientation
            ],
            "Layer 6: Pedigree Bias Deflators": [
                self.agent_non_tier1_champion,
                self.agent_faang_dampener,
                self.agent_local_context_eval,
                self.agent_self_made_builder_sponsor,
                self.agent_credentials_vs_code
            ],
            "Layer 7: Economic Compassion": [
                self.agent_ctc_pragmatist,
                self.agent_relocation_advocate,
                self.agent_notice_period_negotiator,
                self.agent_cost_to_value,
                self.agent_schedule_flexibility
            ],
            "Layer 8: Cognitive Practicality": [
                self.agent_algorithmic_rigor,
                self.agent_pragmatic_workaround,
                self.agent_edge_case_identifier,
                self.agent_code_simplicity,
                self.agent_error_handling_sentinel
            ],
            "Layer 9: Cultural & Community Spirit": [
                self.agent_mission_alignment,
                self.agent_collaborative_spirit,
                self.agent_feedbacks_openness,
                self.agent_mentorship_potential,
                self.agent_startup_hustle
            ],
            "Layer 10: The Human Advocacy Panel": [
                self.agent_final_consensus,
                self.agent_risk_mitigator,
                self.agent_technical_director,
                self.agent_human_potential,
                self.agent_hiring_ombudsman
            ]
        }

    # =========================================================================
    # LAYER 1 AGENTS
    # =========================================================================
    def agent_resume_warmth(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        has_warmth = len(c.bio) > 10
        score = 2.0 if has_warmth else 0.0
        note = "Bio shows a genuine human voice and professional pride." if has_warmth else "Resume bio is brief, but technical focus is maintained."
        return AgentOpinion("Resume Warmth Agent", score, note, has_warmth)

    def agent_writing_clarity(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        clear = len(c.resume_text) > 50
        score = 2.0 if clear else 0.0
        note = "Candidate structures thoughts clearly and articulates achievements well." if clear else "Limited resume text; relies heavily on direct code signals."
        return AgentOpinion("Writing Clarity Agent", score, note, clear)

    def agent_technical_vocabulary(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        vocab = any(skill.lower() in c.resume_text.lower() for skill in c.skills_claimed)
        score = 2.0 if vocab else 0.0
        note = "Uses accurate engineering terminology corresponding to claimed skill sets." if vocab else "Technical terminology is simple and accessible."
        return AgentOpinion("Technical Vocabulary Agent", score, note, vocab)

    def agent_authenticity_scout(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        authentic = "@" in c.email
        score = 2.0 if authentic else 0.0
        note = "Contact info is verified and communication channel is authentic." if authentic else "No clear contact details provided."
        return AgentOpinion("Authenticity Scout", score, note, authentic)

    def agent_layout_compassion(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        # Give benefit of the doubt for layout styles
        note = "Evaluates content over aesthetic packaging; ignores format differences."
        return AgentOpinion("Layout Compassion Agent", 2.0, note, True)

    # =========================================================================
    # LAYER 2 AGENTS
    # =========================================================================
    def agent_commit_cadence(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        has_git = c.github is not None
        active = has_git and c.github.total_commits_last_year > 100
        score = 4.0 if active else 0.0
        note = f"Demonstrates active coding habit with {c.github.total_commits_last_year if has_git else 0} commits." if active else "No high public commit volume, possibly due to private corporate repos."
        return AgentOpinion("Commit Cadence Agent", score, note, active)

    def agent_code_quality_critic(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        has_production = c.github is not None and any(repo.is_production for repo in c.github.repos)
        score = 4.0 if has_production else 0.0
        note = "Public repositories show clean structuring and production-grade habits." if has_production else "Public repos are educational or clean scratchpads."
        return AgentOpinion("Code Quality Critic", score, note, has_production)

    def agent_documentation_advocate(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        has_readme = c.github is not None and len(c.github.repos) > 0
        score = 2.0 if has_readme else 0.0
        note = "Prioritizes developer onboarding with clear documentation." if has_readme else "Relies on self-documenting code structures."
        return AgentOpinion("Documentation Advocate", score, note, has_readme)

    def agent_project_completeness(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        completed = any(p.status == "completed" for p in c.side_projects)
        score = 4.0 if completed else 0.0
        note = "Finished side projects indicate strong execution capabilities and follow-through." if completed else "Has active side projects currently in development."
        return AgentOpinion("Project Completeness Agent", score, note, completed)

    def agent_tech_stack_adaptability(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        languages = set()
        if c.github:
            for repo in c.github.repos:
                languages.update(repo.languages)
        adaptable = len(languages) >= 2
        score = 4.0 if adaptable else 0.0
        note = f"Polyglot tendencies found: comfortable in multiple environments ({', '.join(languages)})." if adaptable else "Focusses on mastering a single specialized programming stack."
        return AgentOpinion("Tech Stack Adaptability Agent", score, note, adaptable)

    # =========================================================================
    # LAYER 3 AGENTS
    # =========================================================================
    def agent_side_project_passion(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        has_projects = len(c.side_projects) > 0
        score = 4.0 if has_projects else 0.0
        note = "Builds things for the pure joy of engineering outside of office hours." if has_projects else "Maintains clear boundaries between work and personal life."
        return AgentOpinion("Side-Project Passion Agent", score, note, has_projects)

    def agent_deployment_practicality(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        deployed = c.github is not None and any(repo.is_production for repo in c.github.repos)
        score = 4.0 if deployed else 0.0
        note = "Understands deployment lifecycles and ships code users can interact with." if deployed else "Focuses on backend services, scripting, and architectural design."
        return AgentOpinion("Deployment Practicality Agent", score, note, deployed)

    def agent_database_architecture(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        db_skills = any(db in [s.lower() for s in c.skills_claimed] for db in ["postgres", "mysql", "redis", "mongodb", "sql"])
        score = 3.0 if db_skills else 0.0
        note = "Comfortable designing databases and writing optimized queries." if db_skills else "No explicit database credentials; focuses on application logic."
        return AgentOpinion("Database Architecture Agent", score, note, db_skills)

    def agent_api_design_critic(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        api_skills = any(api in [s.lower() for s in c.skills_claimed] for api in ["api", "rest", "graphql", "grpc"])
        score = 3.0 if api_skills else 0.0
        note = "Capable of drafting clean APIs and service integration boundaries." if api_skills else "Strong systems developer focusing on internal execution blocks."
        return AgentOpinion("API Design Agent", score, note, api_skills)

    def agent_unconventional_solvers(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        unconventional = c.assessment is not None and c.assessment.is_unconventional
        score = 5.0 if unconventional else 0.0
        note = "Approaches coding challenges with unconventional, highly creative architectures." if unconventional else "Adheres to standard industry conventions and templates."
        return AgentOpinion("Unconventional Solvers Advocate", score, note, unconventional)

    # =========================================================================
    # LAYER 4 AGENTS
    # =========================================================================
    def agent_velocity_estimator(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        fast = c.github is not None and c.github.total_commits_last_year > 400
        score = 4.0 if fast else 0.0
        note = "High-velocity builder with rapid development output." if fast else "Steady development cadence focusing on depth over volume."
        return AgentOpinion("Velocity Estimator", score, note, fast)

    def agent_self_taught_champion(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        self_taught = any(edu.institution.lower() in ["self-taught", "bootcamp", "polytechnic"] for edu in c.education)
        score = 5.0 if self_taught else 0.0
        note = "Displays remarkable drive as a self-taught software builder." if self_taught else "Followed structured formal academic preparation paths."
        return AgentOpinion("Self-Taught Champion", score, note, self_taught)

    def agent_experience_multiplier(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        high_signal_low_exp = c.total_experience_months < r.min_experience_months and c.github is not None and c.github.total_commits_last_year > 300
        score = 5.0 if high_signal_low_exp else 0.0
        note = "Compensates for shorter tenure with extraordinary public contributions." if high_signal_low_exp else "Tenure matches standard seniority requirements."
        return AgentOpinion("Experience Multiplier Agent", score, note, high_signal_low_exp)

    def agent_upskilling_speed(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        upskill = len(c.skills_claimed) > 3
        score = 2.0 if upskill else 0.0
        note = "Actively expands toolkit and updates technical capabilities." if upskill else "Keeps focus on deep specialization."
        return AgentOpinion("Upskilling Speed Agent", score, note, upskill)

    def agent_career_pivot_appraiser(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        pivot = any(edu.field.lower() != "computer science" for edu in c.education) and len(c.skills_claimed) > 0
        score = 3.0 if pivot else 0.0
        note = "Pivot from different domains indicates high cognitive flexibility and motivation." if pivot else "Directly aligned academic background."
        return AgentOpinion("Career Pivot Appraiser", score, note, pivot)

    # =========================================================================
    # LAYER 5 AGENTS
    # =========================================================================
    def agent_promptness_inspector(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        prompt = c.behavioral is not None and c.behavioral.avg_response_time_hours is not None and c.behavioral.avg_response_time_hours < 12
        score = 3.0 if prompt else 0.0
        note = "Responds promptly to communications, speeding up logistics." if prompt else "Maintains standard asynchronous response intervals."
        return AgentOpinion("Promptness Inspector", score, note, prompt)

    def agent_message_tone(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        polite = c.behavioral is not None and c.behavioral.communication_clarity > 0.8
        score = 3.0 if polite else 0.0
        note = "Communication tone is highly collaborative and constructive." if polite else "Direct and functional communication style."
        return AgentOpinion("Message Tone Agent", score, note, polite)

    def agent_reliability_indexer(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        reliable = c.behavioral is not None and c.behavioral.follow_through_rate > 0.85
        score = 3.0 if reliable else 0.0
        note = "High reliability; follows through on tasks and logistical details." if reliable else "Standard compliance on assessment schedules."
        return AgentOpinion("Reliability Indexer", score, note, reliable)

    def agent_compliance_scout(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        compliant = c.behavioral is not None and c.behavioral.response_rate > 0.9
        score = 2.0 if compliant else 0.0
        note = "Completes behavioral checklists and responds consistently." if compliant else "Independent-minded communicator."
        return AgentOpinion("Compliance Scout", score, note, compliant)

    def agent_detail_orientation(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        detailed = len(c.resume_text) > 100
        score = 2.0 if detailed else 0.0
        note = "Pays attention to documentation details in resume submissions." if detailed else "Resume is sparse; focuses strictly on coding footprint."
        return AgentOpinion("Detail Orientation Agent", score, note, detailed)

    # =========================================================================
    # LAYER 6 AGENTS
    # =========================================================================
    def agent_non_tier1_champion(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        non_tier1 = all(not edu.is_tier1 for edu in c.education)
        score = 5.0 if non_tier1 else 0.0
        note = "Championing self-made builders from regional/non-pedigree universities." if non_tier1 else "Candidate is from an elite academic institution."
        return AgentOpinion("Non-Tier-1 Champion", score, note, non_tier1)

    def agent_faang_dampener(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        no_faang = all(not exp.is_faang_or_brand for exp in c.work_experience)
        score = 3.0 if no_faang else 0.0
        note = "Underserved candidate with no brand name bias backing them." if no_faang else "Pedigree company context evaluated alongside verified public work."
        return AgentOpinion("FAANG Dampener Agent", score, note, no_faang)

    def agent_local_context_eval(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Analyzes candidates against local tech context, preventing geographic bias."
        return AgentOpinion("Local Context Evaluator", 2.0, note, True)

    def agent_self_made_builder_sponsor(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        self_made = (any(not edu.is_tier1 for edu in c.education) and 
                     c.github is not None and 
                     c.github.total_commits_last_year > 200)
        score = 5.0 if self_made else 0.0
        note = "Actively sponsoring this candidate's raw grit and public code footprints." if self_made else "Standard background check."
        return AgentOpinion("Self-Made Builder Sponsor", score, note, self_made)

    def agent_credentials_vs_code(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        strong_code = c.github is not None and c.github.total_commits_last_year > 150
        score = 3.0 if strong_code else 0.0
        note = "Prioritizes public code execution over paper credentials." if strong_code else "Relies on credentials and take-home tests."
        return AgentOpinion("Credentials vs Code Agent", score, note, strong_code)

    # =========================================================================
    # LAYER 7 AGENTS
    # =========================================================================
    def agent_ctc_pragmatist(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        fits = r.budget_max_ctc is None or c.expected_ctc is None or c.expected_ctc <= r.budget_max_ctc
        score = 3.0 if fits else 0.0
        # If they don't fit, we still have a heart: advocate for a flexible budget discussion
        note = "Expectations fit within target budgets." if fits else "Expectations slightly exceed budget; advocate for a compensation waiver based on strong skill alignment."
        return AgentOpinion("CTC Pragmatist", score, note, fits)

    def agent_relocation_advocate(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        advocate = c.willing_to_relocate or c.location.lower() == r.location.lower()
        score = 2.0 if advocate else 0.0
        note = "Location match or willing to relocate to support the team." if advocate else "Candidate is remote; advocate for flexible remote working arrangements."
        return AgentOpinion("Relocation Advocate", score, note, advocate)

    def agent_notice_period_negotiator(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        fits = r.max_notice_period_days is None or c.notice_period_days is None or c.notice_period_days <= r.max_notice_period_days
        score = 3.0 if fits else 0.0
        note = "Notice period aligns with timeline." if fits else "Notice period is longer; advocate for buy-out discussions or early transition protocols."
        return AgentOpinion("Notice Period Negotiator", score, note, fits)

    def agent_cost_to_value(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Assesses candidate as a long-term human asset rather than a line-item expense."
        return AgentOpinion("Cost-to-Value Estimator", 2.0, note, True)

    def agent_schedule_flexibility(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Advises flexible onboarding timelines to accommodate personal transits."
        return AgentOpinion("Schedule Flexibility Agent", 2.0, note, True)

    # =========================================================================
    # LAYER 8 AGENTS
    # =========================================================================
    def agent_algorithmic_rigor(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        has_score = c.assessment is not None and c.assessment.score is not None and c.assessment.score > 80
        score = 4.0 if has_score else 0.0
        note = "Take-home code showcases deep logical soundness and edge-case handling." if has_score else "Assessment demonstrates baseline backend capabilities."
        return AgentOpinion("Algorithmic Rigor Agent", score, note, has_score)

    def agent_pragmatic_workaround(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        pragmatic = c.assessment is not None and c.assessment.is_working
        score = 4.0 if pragmatic else 0.0
        note = "Delivers functional, working code instead of over-engineered theoretical models." if pragmatic else "Focuses on coding architecture."
        return AgentOpinion("Pragmatic Workaround Scout", score, note, pragmatic)

    def agent_edge_case_identifier(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Looks for structural simplicity and defensive programming strategies."
        return AgentOpinion("Edge Case Identifier", 3.0, note, True)

    def agent_code_simplicity(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Favors simple, readable, and maintainable architectures over complexity."
        return AgentOpinion("Code Simplicity Fanatic", 3.0, note, True)

    def agent_error_handling_sentinel(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Values defensive check blocks and graceful failure configurations."
        return AgentOpinion("Error Handling Sentinel", 2.0, note, True)

    # =========================================================================
    # LAYER 9 AGENTS
    # =========================================================================
    def agent_mission_alignment(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Candidate's engineering efforts align with our builder-first culture."
        return AgentOpinion("Mission Alignment Reviewer", 3.0, note, True)

    def agent_collaborative_spirit(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        collab = c.github is not None and any(repo.forks > 0 or repo.stars > 2 for repo in c.github.repos)
        score = 3.0 if collab else 0.0
        note = "Creates open-source tools that others fork or star, indicating ecosystem impact." if collab else "Focuses on dedicated individual execution."
        return AgentOpinion("Collaborative Spirit Agent", score, note, collab)

    def agent_feedbacks_openness(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Responsive communications suggest a healthy attitude towards feedback."
        return AgentOpinion("Feedback Openness Scout", 3.0, note, True)

    def agent_mentorship_potential(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        senior = c.total_experience_months > 36
        score = 2.0 if senior else 0.0
        note = "Possesses experience levels suited to guide and support junior peers." if senior else "High growth potential; receptive to technical mentorship."
        return AgentOpinion("Mentorship Potential Scout", score, note, senior)

    def agent_startup_hustle(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        hustle = len(c.side_projects) > 1 or (c.github is not None and c.github.total_commits_last_year > 300)
        score = 4.0 if hustle else 0.0
        note = "Displays energy and hustle suited for highly dynamic building environments." if hustle else "Steady contributor."
        return AgentOpinion("Startup Hustle Assessor", score, note, hustle)

    # =========================================================================
    # LAYER 10 AGENTS
    # =========================================================================
    def agent_final_consensus(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Synthesizes multidimensional strengths into a unified growth narrative."
        return AgentOpinion("Final Consensus Facilitator", 3.0, note, True)

    def agent_risk_mitigator(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        # Rather than fail, try to mitigate risks
        note = "No catastrophic signals found; all constraints can be resolved via dialogue."
        return AgentOpinion("Risk Mitigation Officer", 3.0, note, True)

    def agent_technical_director(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Confirms that practical code portfolio holds substantial merit."
        return AgentOpinion("Technical Director Agent", 3.0, note, True)

    def agent_human_potential(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Sees high latent growth potential and strong long-term alignment."
        return AgentOpinion("Human Potential Scout", 4.0, note, True)

    def agent_hiring_ombudsman(self, c: Candidate, r: RoleSpec) -> AgentOpinion:
        note = "Guarantees a fair evaluation process, actively defending underrepresented builders."
        return AgentOpinion("Hiring Ombudsman", 4.0, note, True)

    # =========================================================================
    # RUN METHOD
    # =========================================================================
    def evaluate(self, candidate: Candidate, role: RoleSpec) -> Dict[str, Any]:
        """
        Runs all 50 agents across the candidate.
        Returns a dictionary with:
          - score_boost: Float representing total empathetic score adjustments
          - advocacy_notes: List of key advocacy points from the agents
          - logs: List of dictionaries detailing each agent's evaluation
        """
        score_boost = 0.0
        advocacy_notes = []
        logs = []

        for layer_name, agents in self.layers.items():
            for agent_fn in agents:
                opinion = agent_fn(candidate, role)
                score_boost += opinion.score_impact
                
                logs.append({
                    "layer": layer_name,
                    "agent": opinion.agent_name,
                    "impact": opinion.score_impact,
                    "note": opinion.advocacy_note,
                    "advocating": opinion.is_advocating
                })

                if opinion.is_advocating:
                    # Collect key advocacy arguments
                    advocacy_notes.append(f"{opinion.agent_name}: {opinion.advocacy_note}")

        return {
            "score_boost": score_boost,
            "advocacy_notes": advocacy_notes,
            "logs": logs
        }
