import csv
import sys
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

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

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#8a8a8a"))
        # We are in landscape mode: 792 x 612
        self.drawRightString(792 - 40, 15, f"Page {self._pageNumber} of {page_count}  |  Team MeritEngine")
        self.restoreState()

def build_pdf_shortlist():
    csv_path = "team_meritengine.csv"
    pdf_path = "team_meritengine.pdf"

    # Set up landscape layout document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=30, rightMargin=30,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#ffffff"),
        spaceAfter=15
    )

    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#ffffff")
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#d1d5db")
    )

    bold_cell_style = ParagraphStyle(
        "TableBoldCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#ffffff")
    )

    story = []

    # Title
    story.append(Paragraph("MeritEngine.ai — Ranked Candidate Shortlist (Top 100)", title_style))
    story.append(Paragraph("Track 01: Senior AI Engineer founding team match.", ParagraphStyle("DocSub", parent=styles["Normal"], fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#8a8a8a"), spaceAfter=15)))

    # Table data
    table_data = [[
        Paragraph("Rank", header_style),
        Paragraph("Candidate ID", header_style),
        Paragraph("Score", header_style),
        Paragraph("Evaluation Reasoning / Justification Note", header_style)
    ]]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader) # skip header
        for row in reader:
            if not row or len(row) < 4:
                continue
            cid, rank, score, reasoning = row[0], row[1], row[2], row[3]
            table_data.append([
                Paragraph(rank, bold_cell_style),
                Paragraph(cid, bold_cell_style),
                Paragraph(score, cell_style),
                Paragraph(reasoning, cell_style)
            ])

    # 792 - 60 (margins) = 732 total width
    col_widths = [45, 95, 55, 537]
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#2a2a2a")),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#141414")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#0a0a0a"), colors.HexColor("#0f1013")]),
    ]))
    
    story.append(t)

    # We want a dark background canvas
    def draw_bg(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFillColor(colors.HexColor("#0a0a0a"))
        canvas_obj.rect(0, 0, 792, 612, fill=True, stroke=False)
        canvas_obj.restoreState()

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=draw_bg, onLaterPages=draw_bg)
    print("PDF Shortlist successfully compiled: team_meritengine.pdf")

if __name__ == "__main__":
    build_pdf_shortlist()
