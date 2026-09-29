"""Professional DOCX legal document generator for LegalEase."""

import io
import os
import re
from typing import List, Optional, Union
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from .sanitizer import clean_text_for_document


def _set_cell_background(cell, hex_color: str):
    """Set the background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell padding (in twips: 20 twips = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def generate_docx(
    document_text: str,
    document_title: str = "LEGAL AGREEMENT",
    effective_date: Optional[str] = None,
    parties: Optional[str] = None,
    terms_list: Optional[List[str]] = None,
    logo_bytes: Optional[Union[bytes, io.BytesIO]] = None,
) -> io.BytesIO:
    """Generate a production-quality, beautifully formatted DOCX legal document.

    Formatting:
    - 1-inch standard legal margins
    - Times New Roman typography
    - Formal title and subtitle
    - Header branding / logo support
    - Formatted terms table with shaded headers
    - Professional headings and paragraph spacing
    - Formatted dual-column signature execution block
    - Running headers and footers with disclaimer
    """
    doc = Document()

    # 1. Page Margins (Standard 1.0 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

        # Configure Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(f"LegalEase Draft -- {document_title}")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(120, 120, 120)

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run(
            "Drafted with LegalEase AI Drafting Assistance | Strictly Subject to Legal Professional Review"
        )
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8)
        frun.font.italic = True
        frun.font.color.rgb = RGBColor(140, 140, 140)

    # 2. Base Style Customization
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    # 3. Optional Logo Insertion
    if logo_bytes:
        try:
            logo_stream = io.BytesIO(logo_bytes) if isinstance(logo_bytes, bytes) else logo_bytes
            logo_p = doc.add_paragraph()
            logo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_p.paragraph_format.space_before = Pt(0)
            logo_p.paragraph_format.space_after = Pt(12)
            run = logo_p.add_run()
            run.add_picture(logo_stream, width=Inches(1.8))
        except Exception:
            # If logo parsing fails, gracefully proceed without it
            pass

    # 4. Document Title
    clean_title = (document_title or "LEGAL AGREEMENT").upper().strip()
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(6)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run(clean_title)
    run_title.font.name = "Times New Roman"
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    # Subtitle with Effective Date
    if effective_date:
        sub_p = doc.add_paragraph()
        sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_p.paragraph_format.space_before = Pt(0)
        sub_p.paragraph_format.space_after = Pt(18)
        run_sub = sub_p.add_run(f"Effective Date: {effective_date.strip()}")
        run_sub.font.name = "Times New Roman"
        run_sub.font.size = Pt(11)
        run_sub.font.italic = True
        run_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Horizontal Rule (Divider)
    divider_p = doc.add_paragraph()
    divider_p.paragraph_format.space_before = Pt(0)
    divider_p.paragraph_format.space_after = Pt(12)
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pBdr>')
    divider_p._p.get_or_add_pPr().append(pBdr)

    # 5. Core Terms Summary Table (if terms_list provided)
    if terms_list and len(terms_list) > 0:
        table_title_p = doc.add_paragraph()
        table_title_p.paragraph_format.space_before = Pt(12)
        table_title_p.paragraph_format.space_after = Pt(4)
        run_tt = table_title_p.add_run("SCHEDULE A: CORE AGREED PROVISIONS SUMMARY")
        run_tt.font.name = "Times New Roman"
        run_tt.font.size = Pt(11.5)
        run_tt.font.bold = True
        run_tt.font.color.rgb = RGBColor(30, 41, 59)

        table = doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Header Row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].width = Inches(1.2)
        hdr_cells[1].width = Inches(5.3)

        hdr_cells[0].paragraphs[0].text = "Item"
        hdr_cells[1].paragraphs[0].text = "Key Term / Agreed Provision"

        for cell in hdr_cells:
            _set_cell_background(cell, "F1F5F9")
            _set_cell_margins(cell, top=140, bottom=140, left=160, right=160)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(10)
                r.font.bold = True
                r.font.color.rgb = RGBColor(15, 23, 42)

        for idx, term in enumerate(terms_list, 1):
            row_cells = table.add_row().cells
            row_cells[0].width = Inches(1.2)
            row_cells[1].width = Inches(5.3)

            row_cells[0].paragraphs[0].text = f"Clause {idx:02d}"
            row_cells[1].paragraphs[0].text = clean_text_for_document(term)

            for c_idx, cell in enumerate(row_cells):
                bg_color = "FAFAFA" if idx % 2 == 0 else "FFFFFF"
                _set_cell_background(cell, bg_color)
                _set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.15
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(10)
                    r.font.color.rgb = RGBColor(51, 65, 85)

        # Spacing after table
        post_table_p = doc.add_paragraph()
        post_table_p.paragraph_format.space_before = Pt(8)
        post_table_p.paragraph_format.space_after = Pt(8)

    # 6. Parse and Render Operative Legal Text
    cleaned_body = clean_text_for_document(document_text)
    paragraphs_raw = cleaned_body.split("\n")

    in_signature_section = False
    signature_lines: List[str] = []

    heading_pattern = re.compile(
        r"^(?:#{1,4}\s+|SECTION\s+\d+|ARTICLE\s+[IVXLCDM\d]+|CLAUSE\s+\d+|[IVXLCDM]+\.\s+|[A-Z\s]{4,}:?$)",
        re.IGNORECASE
    )

    for line in paragraphs_raw:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for signature section beginning
        if "IN WITNESS WHEREOF" in stripped.upper() or "SIGNATURE PAGE" in stripped.upper():
            in_signature_section = True

        if in_signature_section:
            signature_lines.append(stripped)
            continue

        # Check for Headings
        is_heading = False
        heading_text = stripped
        if stripped.startswith("#"):
            is_heading = True
            heading_text = re.sub(r"^#+\s*", "", stripped)
        elif heading_pattern.match(stripped) and len(stripped) < 90:
            is_heading = True

        if is_heading:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(heading_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42)
        elif stripped.startswith(("- ", "* ", "• ")):
            # Bullet item
            bullet_text = re.sub(r"^[-*•]\s*", "", stripped)
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(bullet_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(30, 30, 30)
        else:
            # Standard legal paragraph
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(stripped)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(30, 30, 30)

    # 7. Signature Block Formatting
    # If the document included an IN WITNESS WHEREOF declaration, add it first
    p_witness = doc.add_paragraph()
    p_witness.paragraph_format.space_before = Pt(16)
    p_witness.paragraph_format.space_after = Pt(8)
    p_witness.paragraph_format.keep_with_next = True
    run_wit = p_witness.add_run(
        "IN WITNESS WHEREOF, the Parties have executed this Agreement by their duly authorized "
        "representatives as of the Effective Date written above."
    )
    run_wit.font.name = "Times New Roman"
    run_wit.font.size = Pt(11)
    run_wit.font.bold = True

    # Render Dual Signature Execution Table
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = False

    sig_cells = sig_table.rows[0].cells
    sig_cells[0].width = Inches(3.2)
    sig_cells[1].width = Inches(3.2)

    # Party 1 Block
    p1 = sig_cells[0].paragraphs[0]
    p1.paragraph_format.space_after = Pt(4)
    r1 = p1.add_run("FOR FIRST PARTY / DISCLOSING PARTY:\n\n")
    r1.font.name = "Times New Roman"
    r1.font.bold = True
    r1.font.size = Pt(10.5)

    r1_sub = p1.add_run(
        "Signature: ___________________________\n\n"
        "Printed Name: ________________________\n\n"
        "Title: _______________________________\n\n"
        "Date: ________________________________"
    )
    r1_sub.font.name = "Times New Roman"
    r1_sub.font.size = Pt(10)

    # Party 2 Block
    p2 = sig_cells[1].paragraphs[0]
    p2.paragraph_format.space_after = Pt(4)
    r2 = p2.add_run("FOR SECOND PARTY / RECEIVING PARTY:\n\n")
    r2.font.name = "Times New Roman"
    r2.font.bold = True
    r2.font.size = Pt(10.5)

    r2_sub = p2.add_run(
        "Signature: ___________________________\n\n"
        "Printed Name: ________________________\n\n"
        "Title: _______________________________\n\n"
        "Date: ________________________________"
    )
    r2_sub.font.name = "Times New Roman"
    r2_sub.font.size = Pt(10)

    # Save document to in-memory bytes buffer
    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)
    return docx_buffer
