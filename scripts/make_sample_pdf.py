"""Generates sample_data/Annual_Revenue_Report_2025.pdf - a small multimodal
demo document with text, a financial table, and a chart image, used to test
the ingestion pipeline end to end."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

OUT = os.path.join(os.path.dirname(__file__), "..", "sample_data", "Annual_Revenue_Report_2025.pdf")
CHART = os.path.join(os.path.dirname(__file__), "..", "sample_data", "revenue_chart.png")

styles = getSampleStyleSheet()
doc = SimpleDocTemplate(OUT, pagesize=letter, topMargin=0.8 * inch)
story = []

# Page 1 - narrative text
story.append(Paragraph("Annual Revenue Report — Fiscal Year 2025", styles["Title"]))
story.append(Spacer(1, 12))
story.append(Paragraph("Executive Summary", styles["Heading2"]))
story.append(Paragraph(
    "The company delivered strong performance in fiscal year 2025, with total revenue "
    "reaching $51.0M, up from $43.2M in fiscal year 2024. This represents year-over-year "
    "growth of approximately 18%, driven primarily by expansion in the Enterprise "
    "Software and Cloud Services segments. Gross margin improved to 62%, compared to "
    "58% in the prior year, reflecting continued operating leverage.",
    styles["Normal"],
))
story.append(Spacer(1, 10))
story.append(Paragraph(
    "Regionally, North America remained the largest market at 54% of total revenue, "
    "while Asia-Pacific was the fastest-growing region, up 31% year-over-year on the "
    "back of new enterprise contracts signed in Q3.",
    styles["Normal"],
))
story.append(PageBreak())

# Page 2 - financial table
story.append(Paragraph("Revenue by Segment (2024 vs 2025)", styles["Heading2"]))
story.append(Spacer(1, 10))
table_data = [
    ["Segment", "FY2024 ($M)", "FY2025 ($M)", "YoY Growth"],
    ["Enterprise Software", "18.5", "23.1", "+24.9%"],
    ["Cloud Services", "14.2", "18.7", "+31.7%"],
    ["Professional Services", "7.1", "6.4", "-9.9%"],
    ["Support & Maintenance", "3.4", "2.8", "-17.6%"],
    ["Total", "43.2", "51.0", "+18.1%"],
]
tbl = Table(table_data, colWidths=[2.1 * inch, 1.3 * inch, 1.3 * inch, 1.2 * inch])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14213d")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f3f4f6")]),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
]))
story.append(tbl)
story.append(PageBreak())

# Page 3 - chart image
story.append(Paragraph("Figure 8 — Revenue by Year", styles["Heading2"]))
story.append(Spacer(1, 10))
story.append(Paragraph(
    "The chart below shows total company revenue from fiscal year 2021 through fiscal "
    "year 2025, illustrating five consecutive years of growth.",
    styles["Normal"],
))
story.append(Spacer(1, 10))
story.append(Image(CHART, width=5.2 * inch, height=3.0 * inch))
story.append(Spacer(1, 10))
story.append(Paragraph(
    "Revenue grew from $28.4M in FY2021 to $51.0M in FY2025, a compound annual growth "
    "rate (CAGR) of approximately 15.7%.",
    styles["Normal"],
))

doc.build(story)
print(f"Wrote {OUT}")
