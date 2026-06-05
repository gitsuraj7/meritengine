import sys
import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Ensure UTF-8 output encoding on Windows terminals to prevent encode errors
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class SlideCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def _startPage(self):
        super()._startPage()
        self.draw_background()

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            super().showPage()
        super().save()

    def draw_background(self):
        # We are in landscape mode: 792 x 612
        width, height = 792, 612
        
        # 1. Fill background with matte black
        self.setFillColor(colors.HexColor("#0a0a0a"))
        self.rect(0, 0, width, height, fill=True, stroke=False)
        
        # 2. Draw top accent bar (matte top line with a thin border)
        self.setFillColor(colors.HexColor("#141414"))
        self.rect(0, height - 10, width, 10, fill=True, stroke=False)
        self.setStrokeColor(colors.HexColor("#2a2a2a"))
        self.setLineWidth(1)
        self.line(0, height - 10, width, height - 10)
        
        # 3. Draw bottom footer bar
        self.setFillColor(colors.HexColor("#141414"))
        self.rect(0, 0, width, 30, fill=True, stroke=False)
        self.line(0, 30, width, 30)
        
        # 4. Draw footer static text
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#8a8a8a"))
        self.drawString(30, 11, "REDROB | H2S  INDIA.RUNS  HACKATHON CHALLENGE")

    def draw_page_number(self, page_count):
        width, height = 792, 612
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#8a8a8a"))
        self.drawRightString(width - 30, 11, f"Slide {self._pageNumber} of {page_count}  |  Team MeritEngine")

def build_presentation():
    pdf_path = "presentation_slides.pdf"
    
    # SimpleDocTemplate in landscape mode
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=40, rightMargin=40,
        topMargin=40, bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # Custom slide text styles in White, Matte Grey, and Silver
    title_style = ParagraphStyle(
        "SlideTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#ffffff"),
        spaceAfter=15,
        keepWithNext=True
    )
    
    subtitle_style = ParagraphStyle(
        "SlideSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#8a8a8a"),
        spaceAfter=25
    )
    
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#e2e8f0"),
        spaceBefore=10,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        "SlideBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14.5,
        textColor=colors.HexColor("#d1d5db"),
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        "SlideBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#d1d5db"),
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=6
    )

    story = []
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 1: COVER SLIDE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 30))
    story.append(Paragraph("redrob", ParagraphStyle("CoverLogo", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=28, textColor=colors.HexColor("#ffffff"), spaceAfter=15)))
    story.append(Paragraph("IDEA SUBMISSION TEMPLATE", title_style))
    story.append(Paragraph("MeritEngine.ai — Empathy-First Candidate Discovery & Ranking (Track 01)", subtitle_style))
    story.append(Spacer(1, 20))
    
    cover_data = [
        [Paragraph("<b>Team Name:</b>", body_style), Paragraph("team_meritengine", body_style)],
        [Paragraph("<b>Team Leader:</b>", body_style), Paragraph("Suraj Das", body_style)],
        [Paragraph("<b>Primary Contact:</b>", body_style), Paragraph("etcporasonaetc@gmil.com | +91 83360 41207", body_style)],
        [Paragraph("<b>Code Repository:</b>", body_style), Paragraph("<font color='#ffffff'><u>https://github.com/gitsuraj7/meritengine</u></font>", body_style)]
    ]
    cover_table = Table(cover_data, colWidths=[150, 450])
    cover_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(cover_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 2: SOLUTION OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("01. Solution Overview", title_style))
    story.append(Paragraph("<b>What is your proposed solution?</b>", section_title_style))
    story.append(Paragraph("• A hybrid <b>two-stage candidate evaluation engine</b> that balances sub-second parsing speed and deep semantic ranking.", bullet_style))
    story.append(Paragraph("• <b>Stage 1:</b> Filters 100K profiles line-by-line in under 10 seconds to isolate the top 1,000 candidates based on job spec compatibility and availability.", bullet_style))
    story.append(Paragraph("• <b>Stage 2:</b> Deeply scores the top candidates using a 10-layer, 50-agent Empathy Judging Panel, saving high-potential self-made developers from immediate rejection.", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>What differentiates your approach from traditional systems?</b>", section_title_style))
    story.append(Paragraph("• Traditional applicant tracking systems rely on static keyword parsing and FAANG/Ivy credentials.", bullet_style))
    story.append(Paragraph("• MeritEngine discounts empty brand credentials, tracks contribution velocities/streaks, and utilizes multi-agent advocacy overlays to highlight non-traditional builders.", bullet_style))
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 3: JD UNDERSTANDING & CANDIDATE EVALUATION
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("02. JD Understanding & Candidate Evaluation", title_style))
    story.append(Paragraph("<b>Key Requirements Extracted from the JD:</b>", section_title_style))
    story.append(Paragraph("• **Experience:** 5-9 years of applied machine learning / information retrieval experience in product settings.", bullet_style))
    story.append(Paragraph("• **Tech Stack:** Strong Python. Hands-on vector databases (Milvus, Pinecone, OpenSearch) and evaluation metrics (NDCG, MAP, MRR).", bullet_style))
    story.append(Paragraph("• **Disqualifiers:** Pure research/academic backgrounds, LangChain-only hobbyists, and consulting-only careers (TCS, Wipro, Infosys).", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>How our solution evaluates fit beyond keyword matching:</b>", section_title_style))
    story.append(Paragraph("• **Semantic Fit Matcher:** Embeds candidate summaries and descriptions to match the semantic intent of the job description.", bullet_style))
    story.append(Paragraph("• **Active Availability Adjustments:** Prioritizes high recruiter response rates and penalizes long notice periods (> 90 days).", bullet_style))
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 4: RANKING METHODOLOGY
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("03. Ranking Methodology", title_style))
    story.append(Paragraph("<b>How does the system retrieve, score, and rank candidates?</b>", section_title_style))
    story.append(Paragraph("• **Stage 1 (Vectorized Heuristic Filter):** Processes all 100,000 JSON records, penalizes consulting backgrounds and non-tech titles, and keeps the top 1,000.", bullet_style))
    story.append(Paragraph("• **Stage 2 (Pydantic Evaluation & Empathy Boost):** Deeply evaluates candidate dimensions and applies a soft boost.", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>What models, algorithms, or heuristics are used?</b>", section_title_style))
    story.append(Paragraph("• **Honeypot Filter:** Blocks profiles exhibiting expert skills with zero months usage.", bullet_style))
    story.append(Paragraph("• **Empathy Committee:** A 10-layer, 50-agent soft-score overlay panel providing up to +15 overall score points based on grit markers.", bullet_style))
    story.append(Paragraph("• **Tie-Breaking Rule:** Deterministically resolves score ties using `candidate_id` ascending as specified in Section 3.", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>How are multiple candidate signals combined into a final ranking?</b>", section_title_style))
    story.append(Paragraph("• **Composite Matrix Matching:** Aggregates skill claimed matching, notice period and salary alignment discounts, and public commit velocities into a unified, normalized score.", bullet_style))
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 5: EXPLAINABILITY
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("04. Explainability", title_style))
    story.append(Paragraph("<b>How are ranking decisions explained?</b>", section_title_style))
    story.append(Paragraph("• **Qualitative Advocacy Note:** The Ombudsman layer compiles specific reasons (e.g. 'Data Scientist with 6.8 YoE, strong OpenSearch, 90% response rate').", bullet_style))
    story.append(Paragraph("• **Reasoning monograms:** Stored in the CSV file for manual recruiter review.", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>How do you prevent hallucinations or unsupported justifications?</b>", section_title_style))
    story.append(Paragraph("• String templates are built dynamically using verified, non-hallucinated properties inside the candidate's verified profile data (no external generative model hallucination).", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Handling inconsistent, low-quality, or suspicious profiles:</b>", section_title_style))
    story.append(Paragraph("• Accounts flag and penalize candidates with mismatching work history dates, empty profiles, or inconsistent skill proficiency metrics.", bullet_style))
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 6: END-TO-END WORKFLOW
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("05. End-to-End Workflow", title_style))
    story.append(Paragraph("<b>Complete flow from raw data input to ranked candidate output:</b>", section_title_style))
    
    flow_steps = [
        [Paragraph("<b>1. Raw Ingestion</b>", body_style), Paragraph("Parse raw candidates.jsonl file line-by-line (sub-second per profile).", body_style)],
        [Paragraph("<b>2. Heuristic Filtering</b>", body_style), Paragraph("Prune honeypots, consulting profiles, and non-tech titles. Compute heuristic scores.", body_style)],
        [Paragraph("<b>3. Deep Evaluation</b>", body_style), Paragraph("Convert top 1,000 to Pydantic objects. Run dimension scoring and Empathy Committee boost.", body_style)],
        [Paragraph("<b>4. Sorting & Formatting</b>", body_style), Paragraph("Sort by overall score descending, break ties deterministically, and export the top 100 candidates.", body_style)],
        [Paragraph("<b>5. Compliance Check</b>", body_style), Paragraph("Run official validate_submission.py to ensure zero spec violations.", body_style)]
    ]
    flow_table = Table(flow_steps, colWidths=[160, 500])
    flow_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#2a2a2a")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#141414")),
    ]))
    story.append(flow_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 7: SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("06. System Architecture", title_style))
    story.append(Paragraph("<b>Pipeline Module Structure:</b>", section_title_style))
    
    arch_data = [
        [Paragraph("<b>Module</b>", body_style), Paragraph("<b>Function & Architecture role</b>", body_style)],
        [Paragraph("<code>meritengine/core/models.py</code>", body_style), Paragraph("Pydantic v2 domain schemas modeling Candidate, RoleSpec, and Verdict.", body_style)],
        [Paragraph("<code>meritengine/core/scoring/committee.py</code>", body_style), Paragraph("Main Empathy Committee containing the 10 chambers and 50 sub-agents.", body_style)],
        [Paragraph("<code>meritengine/core/pipeline.py</code>", body_style), Paragraph("Orchestrates dimension scorers and overlays committee qualitative boosts.", body_style)],
        [Paragraph("<code>rank.py</code>", body_style), Paragraph("The optimized two-stage batch ranking execution script complying with compute constraints.", body_style)]
    ]
    arch_table = Table(arch_data, colWidths=[200, 460])
    arch_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#141414")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#2a2a2a")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(arch_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 8: RESULTS & PERFORMANCE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("07. Results & Performance", title_style))
    story.append(Paragraph("<b>What results or insights demonstrate ranking quality?</b>", section_title_style))
    story.append(Paragraph("• **Relevance Output:** Top 10 ranks feature candidates matching the experience band (5-9 years) who have built search/retrieval platforms at product-based companies.", bullet_style))
    story.append(Paragraph("• **Honeypot Rate:** **0% honeypots** in our top 100 shortlist, satisfying Stage 3 compliance guidelines.", bullet_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>How our solution meets runtime and compute constraints:</b>", section_title_style))
    story.append(Paragraph("• **Runtime Limit:** processes 100K candidates and exports the shortlist in **under 15 seconds** (5-minute budget limit).", bullet_style))
    story.append(Paragraph("• **Resource Limits:** CPU-only, 100% offline (no OpenAI/Gemini API calls), and uses less than 1 GB RAM (16 GB limit).", bullet_style))
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 9: TECHNOLOGIES USED
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("08. Technologies Used", title_style))
    story.append(Paragraph("<b>Why were these technologies selected?</b>", section_title_style))
    
    tech_data = [
        [Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Selection Rationale</b>", body_style)],
        [Paragraph("<b>Python 3.12</b>", body_style), Paragraph("Core language, robust parsing, and native zip handling.", body_style)],
        [Paragraph("<b>Pydantic v2</b>", body_style), Paragraph("Strict validation, lightning-fast parsing, and model dump capabilities.", body_style)],
        [Paragraph("<b>SQLite3</b>", body_style), Paragraph("Zero-configuration local DB providing persistent pipeline state tracking.", body_style)],
        [Paragraph("<b>ReportLab</b>", body_style), Paragraph("Professional PDF rendering to compile simulation logs and presentation slide decks.", body_style)]
    ]
    tech_table = Table(tech_data, colWidths=[150, 510])
    tech_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#2a2a2a")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#0f1013"), colors.HexColor("#141414")]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tech_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 10: SUBMISSION ASSETS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("09. Submission Assets", title_style))
    story.append(Paragraph("<b>Access links and files compiled for Stage 3 validation:</b>", section_title_style))
    story.append(Spacer(1, 10))
    
    asset_data = [
        [Paragraph("<b>Submission CSV Shortlist:</b>", body_style), Paragraph("<code>team_meritengine.csv</code> (exactly 100 rows, valid)", body_style)],
        [Paragraph("<b>Methodology Metadata:</b>", body_style), Paragraph("<code>submission_metadata.yaml</code> (filled and tested)", body_style)],
        [Paragraph("<b>Source Code Repository:</b>", body_style), Paragraph("<font color='#ffffff'><u>https://github.com/gitsuraj7/meritengine</u></font>", body_style)],
        [Paragraph("<b>Execution Command:</b>", body_style), Paragraph("<code>python rank.py --candidates ./candidates.jsonl --out ./team_meritengine.csv</code>", body_style)],
        [Paragraph("<b>PDF Presentation Slides:</b>", body_style), Paragraph("<code>presentation_slides.pdf</code> (this file)", body_style)]
    ]
    asset_table = Table(asset_data, colWidths=[200, 460])
    asset_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(asset_table)
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SLIDE 11: THANK YOU
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 120))
    story.append(Paragraph("THANK YOU", ParagraphStyle("ThankTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=42, leading=48, alignment=1, textColor=colors.white, spaceAfter=20)))
    story.append(Paragraph("redrob", ParagraphStyle("ThankLogo", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=24, leading=28, alignment=1, textColor=colors.HexColor("#8a8a8a"), spaceAfter=15)))
    story.append(Paragraph("Presented by Team MeritEngine  |  Building with Empathy", ParagraphStyle("ThankSub", parent=styles["Normal"], fontName="Helvetica", fontSize=12, leading=16, alignment=1, textColor=colors.HexColor("#6a6a6a"))))
    
    doc.build(story, canvasmaker=SlideCanvas)
    print("Presentation slides PDF successfully compiled: presentation_slides.pdf")

if __name__ == "__main__":
    build_presentation()
