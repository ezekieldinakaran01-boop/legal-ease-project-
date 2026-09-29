"""Unit tests for document generation utilities (TXT, DOCX, PDF, HTML, Sanitizer)."""

import io
import os
import sys
import pytest
from PIL import Image

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from document_utils.sanitizer import clean_text_for_document, sanitize_html, parse_terms_list
from document_utils.txt_generator import generate_txt
from document_utils.docx_generator import generate_docx
from document_utils.pdf_generator import generate_pdf
from document_utils.html_preview import convert_markdown_to_legal_html


@pytest.fixture
def sample_logo_bytes():
    """Create a minimal 100x100 PNG image in memory for testing logo embeds."""
    img = Image.new("RGBA", (100, 100), color=(15, 23, 42, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def sample_legal_text():
    return (
        "SECTION 1. CONFIDENTIAL INFORMATION\n"
        "“Confidential Information” shall refer to all proprietary software, designs, and business records.\n\n"
        "SECTION 2. OBLIGATIONS OF RECEIVING PARTY\n"
        "- Recipient shall preserve confidentiality for 3 years.\n"
        "- Recipient shall not disclose information to third parties without prior written consent.\n\n"
        "SECTION 3. GOVERNING LAW\n"
        "This Agreement shall be governed by the laws of the State of Delaware.\n\n"
        "IN WITNESS WHEREOF, the Parties execute this Agreement."
    )


def test_clean_text_for_document():
    """Verify smart quotes, dashes, and special unicode are cleanly normalized."""
    input_text = "“Smart Quotes” and ‘Single Quotes’ — Em Dash and – En Dash with … ellipsis."
    cleaned = clean_text_for_document(input_text)
    assert '"Smart Quotes"' in cleaned
    assert "'Single Quotes'" in cleaned
    assert " -- " in cleaned
    assert " - " in cleaned
    assert "..." in cleaned


def test_sanitize_html_xss_protection():
    """Verify script tags, iframes, and javascript links are stripped."""
    dangerous = (
        '<div>Legal text <script>alert("hacked")</script> '
        '<iframe src="evil.com"></iframe>'
        '<a href="javascript:stealCookie()">Link</a></div>'
    )
    sanitized = sanitize_html(dangerous)
    assert "<script>" not in sanitized
    assert "alert" not in sanitized
    assert "<iframe" not in sanitized
    assert "javascript:" not in sanitized
    assert "Legal text" in sanitized


def test_parse_terms_list():
    """Verify parsing semicolon-separated and newline-separated terms."""
    # Semicolon separated
    terms_semicolon = (
        "1. Confidentiality for 3 years; "
        "2. Permitted evaluation use only; "
        "- Return of materials within 10 days"
    )
    parsed = parse_terms_list(terms_semicolon)
    assert len(parsed) == 3
    assert parsed[0] == "Confidentiality for 3 years"
    assert parsed[1] == "Permitted evaluation use only"
    assert parsed[2] == "Return of materials within 10 days"

    # Newline separated
    terms_newline = (
        "* Payment net 30\n"
        "* 10% late fee\n"
        "* Mutual indemnity"
    )
    parsed_nl = parse_terms_list(terms_newline)
    assert len(parsed_nl) == 3
    assert "Payment net 30" in parsed_nl[0]


def test_generate_txt(sample_legal_text):
    """Verify plain text generation produces expected headers, sections, and ASCII borders."""
    txt = generate_txt(
        document_text=sample_legal_text,
        document_title="MUTUAL NON-DISCLOSURE AGREEMENT",
        effective_date="2026-10-01",
        parties="Party A: Alpha Corp; Party B: Beta LLC",
        terms_list=["Term 1", "Term 2"],
    )
    assert "MUTUAL NON-DISCLOSURE AGREEMENT" in txt
    assert "Effective Date: 2026-10-01" in txt
    assert "PARTIES INVOLVED:" in txt
    assert "SUMMARY OF CORE AGREED PROVISIONS:" in txt
    assert "END OF DOCUMENT" in txt
    assert "LegalEase AI Drafting Assistant" in txt


def test_generate_docx_without_logo(sample_legal_text):
    """Verify DOCX binary generation without logo."""
    docx_buf = generate_docx(
        document_text=sample_legal_text,
        document_title="EMPLOYMENT CONTRACT",
        effective_date="2026-10-01",
        parties="Employer and Employee",
        terms_list=["Salary $100k", "401k match"],
    )
    assert isinstance(docx_buf, io.BytesIO)
    content = docx_buf.getvalue()
    # Word docx is a zip file starting with PK\x03\x04
    assert content.startswith(b"PK\x03\x04")
    assert len(content) > 1000


def test_generate_docx_with_logo(sample_legal_text, sample_logo_bytes):
    """Verify DOCX generation with embedded logo."""
    docx_buf = generate_docx(
        document_text=sample_legal_text,
        document_title="BRANDED AGREEMENT",
        effective_date="2026-10-01",
        parties="Company and Client",
        terms_list=["Clause A", "Clause B"],
        logo_bytes=sample_logo_bytes,
    )
    content = docx_buf.getvalue()
    assert content.startswith(b"PK\x03\x04")
    assert len(content) > 1000


def test_generate_pdf_without_logo(sample_legal_text):
    """Verify PDF generation without logo produces valid PDF binary."""
    pdf_buf = generate_pdf(
        document_text=sample_legal_text,
        document_title="LEASE AGREEMENT",
        effective_date="2026-10-01",
        parties="Landlord and Tenant",
        terms_list=["Rent $2000/mo", "Security deposit $2000"],
    )
    assert isinstance(pdf_buf, io.BytesIO)
    content = pdf_buf.getvalue()
    assert content.startswith(b"%PDF")
    assert len(content) > 1000


def test_generate_pdf_with_logo(sample_legal_text, sample_logo_bytes):
    """Verify PDF generation with embedded logo."""
    pdf_buf = generate_pdf(
        document_text=sample_legal_text,
        document_title="BRANDED LEASE AGREEMENT",
        effective_date="2026-10-01",
        parties="Landlord and Tenant",
        terms_list=["Rent $2000/mo", "Security deposit $2000"],
        logo_bytes=sample_logo_bytes,
    )
    content = pdf_buf.getvalue()
    assert content.startswith(b"%PDF")
    assert len(content) > 1000


def test_convert_markdown_to_legal_html(sample_legal_text):
    """Verify HTML preview compilation includes styling classes, headers, and disclaimer."""
    html_output = convert_markdown_to_legal_html(
        content=sample_legal_text,
        document_title="SERVICE LEVEL AGREEMENT",
        effective_date="October 1, 2026",
        parties="Provider Inc and Client Corp",
        terms_list=["99.9% Uptime", "24/7 Support"],
    )
    assert "legalease-paper" in html_output
    assert "SERVICE LEVEL AGREEMENT" in html_output
    assert "October 1, 2026" in html_output
    assert "SCHEDULE A: CORE AGREED PROVISIONS" in html_output
    assert "FIRST PARTY / DISCLOSING PARTY" in html_output
    assert "Legal Notice:" in html_output
