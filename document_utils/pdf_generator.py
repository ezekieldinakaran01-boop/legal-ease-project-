"""Professional PDF legal document generator for LegalEase using fpdf2."""

import io
import re
from typing import List, Optional, Union
from PIL import Image
from fpdf import FPDF
from .sanitizer import clean_text_for_document


class LegalPDF(FPDF):
    """Custom FPDF2 class designed for formal legal documentation with headers, footers, and page numbers."""

    def __init__(self, doc_title: str = "LEGAL AGREEMENT", *args, **kwargs):
        super().__init__(orientation="P", unit="mm", format="A4", *args, **kwargs)
        self.doc_title = (doc_title or "LEGAL AGREEMENT").upper().strip()
        self.set_margins(left=20, top=20, right=20)
        self.set_auto_page_break(auto=True, margin=24)

    def header(self):
        """Render running header on pages after the first page."""
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(130, 140, 150)
            # Running header text
            self.cell(
                0,
                6,
                f"LegalEase Draft -- {self.doc_title}",
                align="R",
                new_x="LMARGIN",
                new_y="NEXT"
            )
            # Divider line below header
            self.set_draw_color(220, 226, 235)
            self.set_line_width(0.2)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

    def footer(self):
        """Render professional legal footer with disclaimer and dynamic page count on all pages."""
        self.set_y(-18)
        self.set_draw_color(220, 226, 235)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2.5)

        # Disclaimer line
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(140, 150, 160)
        self.cell(
            0,
            3.5,
            "LegalEase AI Drafting Assistant | Strictly Subject to Legal Professional Review",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT"
        )

        # Dynamic page count (uses alias_nb_pages())
        page_str = f"Page {self.page_no()} of {{nb}}"
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(160, 170, 180)
        self.cell(0, 3.5, page_str, align="C")


def generate_pdf(
    document_text: str,
    document_title: str = "LEGAL AGREEMENT",
    effective_date: Optional[str] = None,
    parties: Optional[str] = None,
    terms_list: Optional[List[str]] = None,
    logo_bytes: Optional[Union[bytes, io.BytesIO]] = None,
) -> io.BytesIO:
    """Generate a production-quality legal PDF document."""
    pdf = LegalPDF(doc_title=document_title)
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. Optional Logo at Document Top
    if logo_bytes:
        try:
            stream = io.BytesIO(logo_bytes) if isinstance(logo_bytes, bytes) else logo_bytes
            img = Image.open(stream)
            # Calculate aspect ratio
            orig_w, orig_h = img.size
            display_w = 32.0  # mm
            display_h = (orig_h / orig_w) * display_w
            # Center logo
            x_pos = (pdf.epw - display_w) / 2 + pdf.l_margin
            pdf.image(img, x=x_pos, y=pdf.get_y(), w=display_w, h=display_h)
            pdf.set_y(pdf.get_y() + display_h + 4)
        except Exception:
            # Gracefully continue if logo cannot be rendered
            pass

    # 2. Document Title
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(15, 23, 42)  # Dark navy/slate
    clean_title = (document_title or "LEGAL AGREEMENT").upper().strip()
    pdf.multi_cell(
        w=pdf.epw,
        h=7,
        text=clean_title,
        align="C",
        new_x="LMARGIN",
        new_y="NEXT"
    )
    pdf.ln(1)

    # 3. Effective Date Subtitle
    if effective_date:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(
            0,
            6,
            f"Effective Date: {effective_date.strip()}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT"
        )
        pdf.ln(2)

    # Header Divider Line
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    # 4. Core Terms Summary Table (if terms provided)
    if terms_list and len(terms_list) > 0:
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 6, "SCHEDULE A: CORE AGREED PROVISIONS SUMMARY", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        col1_w = 26.0  # mm for clause tag
        col2_w = pdf.epw - col1_w

        # Table Header
        pdf.set_fill_color(241, 245, 249)  # #F1F5F9
        pdf.set_draw_color(203, 213, 225)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(col1_w, 7, "  Item", border=1, fill=True)
        pdf.cell(col2_w, 7, "  Key Term / Agreed Provision", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        # Table Rows
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(51, 65, 85)
        for idx, term in enumerate(terms_list, 1):
            bg = (250, 250, 250) if idx % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*bg)
            term_clean = clean_text_for_document(term).strip()

            start_y = pdf.get_y()
            start_x = pdf.get_x()

            # Measure height of term text
            with pdf.rotation(0):
                # Calculate required height for multi_cell
                # Using cell height estimate
                lines_est = max(1, len(term_clean) // 70 + 1)
                row_h = max(7, lines_est * 4.5)

            # Check if row fits on page; if not, add page
            if pdf.get_y() + row_h > (pdf.h - pdf.b_margin):
                pdf.add_page()
                start_y = pdf.get_y()
                start_x = pdf.get_x()

            # Render col 1
            pdf.cell(col1_w, row_h, f"  Clause {idx:02d}", border=1, fill=True)
            # Render col 2
            x_after_c1 = pdf.get_x()
            y_before_c2 = pdf.get_y()
            pdf.multi_cell(
                col2_w,
                row_h / lines_est,
                f" {term_clean}",
                border=1,
                fill=True,
                align="L",
                new_x="LMARGIN",
                new_y="NEXT"
            )

        pdf.ln(5)

    # 5. Operative Body Paragraphs
    cleaned_body = clean_text_for_document(document_text)
    lines = cleaned_body.split("\n")

    heading_pattern = re.compile(
        r"^(?:#{1,4}\s+|SECTION\s+\d+|ARTICLE\s+[IVXLCDM\d]+|CLAUSE\s+\d+|[IVXLCDM]+\.\s+|[A-Z\s]{4,}:?$)",
        re.IGNORECASE
    )

    in_signature_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if "IN WITNESS WHEREOF" in stripped.upper() or "SIGNATURE PAGE" in stripped.upper():
            in_signature_section = True

        if in_signature_section:
            # We handle signature block explicitly below
            continue

        # Heading detection
        is_heading = False
        heading_text = stripped
        if stripped.startswith("#"):
            is_heading = True
            heading_text = re.sub(r"^#+\s*", "", stripped)
        elif heading_pattern.match(stripped) and len(stripped) < 90:
            is_heading = True

        if is_heading:
            # Check page break margin
            if pdf.get_y() > (pdf.h - pdf.b_margin - 20):
                pdf.add_page()
            else:
                pdf.ln(3)

            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(
                pdf.epw,
                5.5,
                heading_text,
                align="L",
                new_x="LMARGIN",
                new_y="NEXT"
            )
            pdf.ln(1)
        elif stripped.startswith(("- ", "* ", "• ")):
            bullet_text = re.sub(r"^[-*•]\s*", "", stripped)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(
                pdf.epw - 4,
                4.8,
                f"*  {bullet_text}",
                align="L",
                new_x="LMARGIN",
                new_y="NEXT"
            )
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(
                pdf.epw,
                4.8,
                stripped,
                align="J",
                new_x="LMARGIN",
                new_y="NEXT"
            )
            pdf.ln(2.2)

    # 6. Formal Signature Execution Section
    # Check if signature block fits; needs ~45mm
    if pdf.get_y() > (pdf.h - pdf.b_margin - 45):
        pdf.add_page()
    else:
        pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(
        pdf.epw,
        5,
        "IN WITNESS WHEREOF, the Parties have caused this Agreement to be executed "
        "by their duly authorized representatives as of the Effective Date.",
        align="L",
        new_x="LMARGIN",
        new_y="NEXT"
    )
    pdf.ln(4)

    # Render Dual Signature Block Columns
    col_w = (pdf.epw - 10) / 2.0
    start_y = pdf.get_y()
    start_x = pdf.l_margin

    # Left Column: Party A
    pdf.set_xy(start_x, start_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(col_w, 5, "ON BEHALF OF PARTY A:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(71, 85, 105)
    pdf.set_x(start_x)
    pdf.cell(col_w, 5, "Signature: __________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(start_x)
    pdf.cell(col_w, 5, "Printed Name: _______________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(start_x)
    pdf.cell(col_w, 5, "Title: ______________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(start_x)
    pdf.cell(col_w, 5, "Date: _______________________________", new_x="LMARGIN", new_y="NEXT")

    # Right Column: Party B
    right_x = start_x + col_w + 10
    pdf.set_xy(right_x, start_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(col_w, 5, "ON BEHALF OF PARTY B:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(71, 85, 105)
    pdf.set_xy(right_x, pdf.get_y())
    pdf.cell(col_w, 5, "Signature: __________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(right_x, pdf.get_y())
    pdf.cell(col_w, 5, "Printed Name: _______________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(right_x, pdf.get_y())
    pdf.cell(col_w, 5, "Title: ______________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(right_x, pdf.get_y())
    pdf.cell(col_w, 5, "Date: _______________________________", new_x="LMARGIN", new_y="NEXT")

    pdf_buffer = io.BytesIO()
    pdf_bytes = pdf.output()
    pdf_buffer.write(pdf_bytes)
    pdf_buffer.seek(0)
    return pdf_buffer
