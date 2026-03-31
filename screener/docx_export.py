"""Generate Word (.docx) reports matching the IOWN template format."""

import io
import os
from pathlib import Path

import requests
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, Emu, RGBColor

# Cache logo bytes
_logo_bytes: bytes | None = None
LOGO_URL = "https://richacarson.github.io/Dashboard/iown-logo.png"

# Colors
C_DARK = RGBColor(0x1A, 0x20, 0x10)
C_MUTED = RGBColor(0x9D, 0xAF, 0x88)
C_GREEN = RGBColor(0x16, 0xA3, 0x4A)
C_GOLD = RGBColor(0xD9, 0x77, 0x06)
C_RED = RGBColor(0xDC, 0x26, 0x26)
C_BLUE = RGBColor(0x25, 0x63, 0xEB)

FOOTER_TEXT = (
    'Paradiem, LLC dba Intentional Ownership (\u201CIOWN\u201D) is a registered '
    'investment advisor. The information provided is for educational and '
    'informational purposes only and does not constitute investment advice.'
)


def _get_logo() -> bytes | None:
    global _logo_bytes
    if _logo_bytes is not None:
        return _logo_bytes
    logo_path = Path("templates/iown-logo.png")
    if logo_path.exists():
        _logo_bytes = logo_path.read_bytes()
        return _logo_bytes
    try:
        resp = requests.get(LOGO_URL, timeout=10)
        resp.raise_for_status()
        _logo_bytes = resp.content
        logo_path.write_bytes(_logo_bytes)
        return _logo_bytes
    except Exception:
        return None


def _add_run(paragraph, text: str, size: Pt, bold: bool = False, color=C_DARK):
    run = paragraph.add_run(text)
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return run


def _rec_color(rec: str) -> RGBColor:
    rec = rec.upper()
    if rec == "BUY":
        return C_GREEN
    if rec == "HOLD":
        return C_GOLD
    if rec == "SELL":
        return C_RED
    return C_BLUE


def _section_header(doc: Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    _add_run(p, text, Pt(8.5), bold=True)


def _score_line(doc: Document, label: str, tag: str, score, analysis: str):
    """Add a dimension score block (label + tag, score, analysis)."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(1)
    _add_run(p, f"{label}  ", Pt(11))
    _add_run(p, tag, Pt(11), bold=True)

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(2)
    _add_run(p2, str(score), Pt(11), bold=True)

    if analysis:
        p3 = doc.add_paragraph()
        p3.paragraph_format.space_before = Pt(0)
        p3.paragraph_format.space_after = Pt(4)
        _add_run(p3, analysis, Pt(9))


def _bullet(doc: Document, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    _add_run(p, text, Pt(10))


def generate_docx(report: dict) -> bytes:
    """Generate a Word doc from a report dict, return bytes."""
    doc = Document()

    # Page margins (0.5 inch all around, matching template)
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    # Logo
    logo = _get_logo()
    if logo:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(io.BytesIO(logo), width=Inches(1.5))

    ticker = report.get("ticker", "")
    name = report.get("name", "")
    sleeve = report.get("sleeve", "")
    rec = report.get("recommendation", "")
    score = report.get("overall_score", 0)
    screen_date = report.get("screen_date", "")
    profile = report.get("profile", {})
    excellence = report.get("excellence_evaluation", {})
    ai_res = report.get("ai_resilience", {})
    ig = report.get("infinite_game", {})
    faith = report.get("faith_alignment", {})

    inspire_score = faith.get("inspire_impact_score", "N/A")
    mindset = ig.get("mindset", "")

    # Title line
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    _add_run(p, f"{ticker}  ", Pt(27), bold=True)
    _add_run(p, name, Pt(27), bold=True)

    # Subtitle line
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    parts = [sleeve.upper() + " SLEEVE", screen_date]
    if inspire_score is not None and inspire_score != "N/A":
        parts.append(f"Inspire: {inspire_score}")
    if mindset:
        parts.append(mindset)
    _add_run(p, " \u00b7 ".join(parts), Pt(9), bold=True)

    # Recommendation badge
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    _add_run(p, rec, Pt(11), bold=True, color=_rec_color(rec))

    # Overall score
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    _add_run(p, str(score), Pt(36), bold=True)
    _add_run(p, " / ", Pt(13.5))
    _add_run(p, "100", Pt(11))

    # Company Profile
    _section_header(doc, "Company Profile")
    sector = profile.get("sector", "")
    industry = profile.get("industry", "")
    exchange = profile.get("exchange", "")
    country = profile.get("country", "")
    meta_parts = [x for x in [sector, industry, exchange, country] if x]
    if meta_parts:
        p = doc.add_paragraph()
        _add_run(p, " \u00b7 ".join(meta_parts), Pt(9), bold=True)

    desc = profile.get("description", "")
    if desc:
        p = doc.add_paragraph()
        _add_run(p, desc, Pt(10))

    employees = profile.get("employees")
    website = profile.get("website", "")
    info_parts = []
    if employees:
        info_parts.append(f"{employees:,} Employees")
    if website:
        info_parts.append(website)
    if info_parts:
        p = doc.add_paragraph()
        _add_run(p, " \u00b7 ".join(info_parts), Pt(9), bold=True)

    # Excellence Evaluation
    _section_header(doc, "Excellence Evaluation \u2014 Think Like an Owner (50%)")

    innov = excellence.get("innovation", {})
    _score_line(doc, "Innovation", innov.get("label", ""),
                innov.get("score", 0), innov.get("analysis", ""))

    insp = excellence.get("inspiration", {})
    _score_line(doc, "Inspiration", insp.get("label", ""),
                insp.get("score", 0), insp.get("analysis", ""))

    infra = excellence.get("infrastructure", {})
    _score_line(doc, "Infrastructure", infra.get("label", ""),
                infra.get("score", 0), infra.get("analysis", ""))

    # Infinite Game
    _section_header(doc, "Finite vs Infinite Game \u2014 Sinek (25%)")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    _add_run(p, f"Mindset: {mindset}    ", Pt(11))
    _add_run(p, f"Overall: {ig.get('overall', 0)}", Pt(11), bold=True)
    _add_run(p, " /10", Pt(11))

    summary = ig.get("summary", "")
    if summary:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        _add_run(p, summary, Pt(9))

    for dim in ["just_cause", "trusting_teams", "worthy_rivals",
                "existential_flexibility", "courage_to_lead"]:
        d = ig.get(dim, {})
        label = dim.replace("_", " ").title()
        _score_line(doc, label, "", d.get("score", 0), d.get("analysis", ""))

    # Investment Thesis
    _section_header(doc, "Investment Thesis")
    thesis = report.get("investment_thesis", "")
    if thesis:
        p = doc.add_paragraph()
        _add_run(p, thesis, Pt(10))
    thesis2 = report.get("thesis_continued", "")
    if thesis2:
        p = doc.add_paragraph()
        _add_run(p, thesis2, Pt(10))

    # Catalysts
    catalysts = report.get("key_catalysts", [])
    if catalysts:
        _section_header(doc, "Key Catalysts")
        for c in catalysts:
            _bullet(doc, f"\u2022  {c}")

    # Risks
    risks = report.get("key_risks", [])
    if risks:
        _section_header(doc, "Key Risks")
        for r in risks:
            _bullet(doc, f"\u2022  {r}")

    # AI Resilience
    _section_header(doc, "AI Resilience (25%)")
    _score_line(doc, "AI Resilience", ai_res.get("label", ""),
                ai_res.get("score", 0), ai_res.get("analysis", ""))

    # Faith Alignment
    _section_header(doc, "Faith Alignment \u2014 Inspire Insight")
    p = doc.add_paragraph()
    label = faith.get("label", "")
    _add_run(p, f"Inspire Impact Score: {inspire_score}    ", Pt(11))
    _add_run(p, label, Pt(11), bold=True)

    neg = faith.get("negative_attributions", [])
    if neg:
        p = doc.add_paragraph()
        _add_run(p, f"Negative: {', '.join(neg)}", Pt(11))

    pos = faith.get("positive_attributions", [])
    if pos:
        p = doc.add_paragraph()
        _add_run(p, f"Positive: {', '.join(pos)}", Pt(11))

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    _add_run(p, "Source: Inspire Insight", Pt(7.5))

    # Resources
    sources = report.get("sources", [])
    if sources:
        _section_header(doc, "Resources")
        for i, s in enumerate(sources, 1):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            _add_run(p, f"{i}. ", Pt(7.5), bold=True)
            _add_run(p, s, Pt(8.5))

    # Footer
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(16)
    _add_run(p, FOOTER_TEXT, Pt(8), color=C_MUTED)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
