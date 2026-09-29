"""Plain text document generator for LegalEase."""

from typing import List, Optional
from .sanitizer import clean_text_for_document


def generate_txt(
    document_text: str,
    document_title: str = "LEGAL AGREEMENT",
    effective_date: Optional[str] = None,
    parties: Optional[str] = None,
    terms_list: Optional[List[str]] = None,
) -> str:
    """Generate a cleanly formatted, professional plain text legal document.

    Formats the document with standard legal document separators, centered headers,
    structured terms section if applicable, signature lines, and drafting disclaimer.
    """
    cleaned_body = clean_text_for_document(document_text).strip()
    title_upper = (document_title or "LEGAL DOCUMENT").upper().strip()

    line_width = 80
    border = "=" * line_width
    sub_border = "-" * line_width

    lines: List[str] = []
    lines.append(border)
    lines.append(title_upper.center(line_width))
    if effective_date:
        lines.append(f"Effective Date: {effective_date.strip()}".center(line_width))
    lines.append(border)
    lines.append("")

    if parties:
        lines.append("PARTIES INVOLVED:")
        lines.append(sub_border)
        lines.append(clean_text_for_document(parties).strip())
        lines.append("")

    if terms_list and len(terms_list) > 0:
        lines.append("SUMMARY OF CORE AGREED PROVISIONS:")
        lines.append(sub_border)
        for idx, term in enumerate(terms_list, 1):
            lines.append(f"  [{idx:02d}] {clean_text_for_document(term).strip()}")
        lines.append("")

    lines.append(sub_border)
    lines.append("DOCUMENT TEXT & OPERATIVE PROVISIONS".center(line_width))
    lines.append(sub_border)
    lines.append("")
    lines.append(cleaned_body)
    lines.append("")
    lines.append(border)
    lines.append("END OF DOCUMENT".center(line_width))
    lines.append("LegalEase AI Drafting Assistant | Subject to Professional Legal Review".center(line_width))
    lines.append(border)

    return "\n".join(lines)
