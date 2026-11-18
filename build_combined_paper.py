import os
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "Results"

def format_markdown_line_for_reportlab(text: str) -> str:
    safe = escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"\*(.+?)\*", r"<i>\1</i>", safe)
    return safe

def export_to_pdf(markdown_text: str, pdf_path: Path):
    print(f"Building clean PDF -> {pdf_path}...")
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PaperTitle",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        spaceAfter=14,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=12,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading3"],
        fontName="Times-BoldItalic",
        fontSize=10.5,
        leading=13,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "PaperBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13.5,
        alignment=TA_JUSTIFY,
        spaceAfter=7,
    )
    bullet_style = ParagraphStyle(
        "PaperBullet",
        parent=body_style,
        leftIndent=16,
        firstLineIndent=-8,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "PaperCode",
        fontName="Courier",
        fontSize=7.2,
        leading=9.0,
        backColor=colors.HexColor("#F5F7FA"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8,
    )

    story = []
    first_heading_seen = False

    # Split out fenced ```...``` blocks first so ASCII diagrams & tables stay intact
    parts = re.split(r"(```[\s\S]*?```)", markdown_text)

    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            diagram_text = part[3:-3].strip("\n")
            story.append(Preformatted(diagram_text, code_style))
            continue

        for raw_block in part.split("\n\n"):
            block = raw_block.strip()
            if not block or block == "---":
                continue

            if block.startswith("# "):
                clean = format_markdown_line_for_reportlab(block[2:].strip())
                if not first_heading_seen:
                    story.append(Paragraph(clean, title_style))
                    first_heading_seen = True
                else:
                    story.append(Paragraph(clean, h1_style))
            elif block.startswith("## "):
                clean = format_markdown_line_for_reportlab(block[3:].strip())
                story.append(Paragraph(clean, h1_style))
            elif block.startswith("### "):
                clean = format_markdown_line_for_reportlab(block[4:].strip())
                story.append(Paragraph(clean, h2_style))
            elif block.startswith(("- ", "* ")):
                for line in block.split("\n"):
                    line_clean = re.sub(r"^[-*]\s+", "", line.strip())
                    story.append(Paragraph("• " + format_markdown_line_for_reportlab(line_clean), bullet_style))
            elif re.match(r"^\d+\.\s+", block):
                for line in block.split("\n"):
                    if line.strip():
                        story.append(Paragraph(format_markdown_line_for_reportlab(line.strip()), bullet_style))
            else:
                joined = " ".join(line.strip() for line in block.split("\n"))
                story.append(Paragraph(format_markdown_line_for_reportlab(joined), body_style))

    doc.build(story)
    print(f"Saved clean PDF -> {pdf_path}")

if __name__ == "__main__":
    txt_out = RESULTS_DIR / "FINAL_COMBINED_PAPER.txt"
    pdf_out = RESULTS_DIR / "FINAL_COMBINED_PAPER.pdf"
    export_to_pdf(txt_out.read_text(encoding="utf-8"), pdf_out)