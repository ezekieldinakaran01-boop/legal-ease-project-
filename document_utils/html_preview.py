"""Safe, high-fidelity legal document HTML preview formatter for LegalEase."""

import re
import html
from typing import List, Optional
from .sanitizer import sanitize_html, clean_text_for_document


def convert_markdown_to_legal_html(
    content: str,
    document_title: str = "LEGAL AGREEMENT",
    effective_date: Optional[str] = None,
    parties: Optional[str] = None,
    terms_list: Optional[List[str]] = None,
) -> str:
    """Transform raw legal text or markdown into a pristine, sanitized, SaaS-grade legal brief HTML view.

    The returned HTML is safe from XSS attacks, features typography tailored for contracts,
    and formats clauses, terms tables, and signature blocks in a formal document style.
    """
    safe_title = html.escape((document_title or "LEGAL AGREEMENT").upper().strip())
    safe_date = html.escape((effective_date or "").strip())
    safe_parties = html.escape((parties or "").strip())

    # Pre-clean input
    sanitized_body = sanitize_html(clean_text_for_document(content))

    # Convert paragraphs and headings
    lines = sanitized_body.split("\n")
    formatted_body_lines: List[str] = []
    in_bullet_list = False

    heading_regex = re.compile(
        r"^(?:#{1,4}\s+|SECTION\s+\d+|ARTICLE\s+[IVXLCDM\d]+|CLAUSE\s+\d+|[IVXLCDM]+\.\s+|[A-Z\s]{4,}:?$)",
        re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_bullet_list:
                formatted_body_lines.append("</ul>")
                in_bullet_list = False
            continue

        # Check for headings
        is_heading = False
        level = 2
        h_text = stripped

        if stripped.startswith("###"):
            is_heading = True
            level = 3
            h_text = re.sub(r"^###\s*", "", stripped)
        elif stripped.startswith("##"):
            is_heading = True
            level = 2
            h_text = re.sub(r"^##\s*", "", stripped)
        elif stripped.startswith("#"):
            is_heading = True
            level = 1
            h_text = re.sub(r"^#\s*", "", stripped)
        elif heading_regex.match(stripped) and len(stripped) < 90:
            is_heading = True
            level = 2

        if is_heading:
            if in_bullet_list:
                formatted_body_lines.append("</ul>")
                in_bullet_list = False
            safe_h = html.escape(h_text)
            if level == 1:
                formatted_body_lines.append(f'<h2 class="legal-h1">{safe_h}</h2>')
            elif level == 2:
                formatted_body_lines.append(f'<h3 class="legal-h2">{safe_h}</h3>')
            else:
                formatted_body_lines.append(f'<h4 class="legal-h3">{safe_h}</h4>')
            continue

        # Check for bullet items
        if stripped.startswith(("- ", "* ", "• ")):
            if not in_bullet_list:
                formatted_body_lines.append('<ul class="legal-list">')
                in_bullet_list = True
            raw_item = re.sub(r"^[-*•]\s*", "", stripped)
            safe_item = _inline_markdown(html.escape(raw_item))
            formatted_body_lines.append(f"<li>{safe_item}</li>")
            continue
        else:
            if in_bullet_list:
                formatted_body_lines.append("</ul>")
                in_bullet_list = False

        # Regular legal paragraph
        safe_p = _inline_markdown(html.escape(stripped))
        formatted_body_lines.append(f'<p class="legal-p">{safe_p}</p>')

    if in_bullet_list:
        formatted_body_lines.append("</ul>")

    body_html = "\n".join(formatted_body_lines)

    # Optional Terms Table HTML
    terms_table_html = ""
    if terms_list and len(terms_list) > 0:
        rows = []
        for idx, term in enumerate(terms_list, 1):
            safe_term = html.escape(term)
            rows.append(
                f'<tr>'
                f'<td class="term-col-num">Clause {idx:02d}</td>'
                f'<td class="term-col-text">{safe_term}</td>'
                f'</tr>'
            )
        terms_table_html = f"""
        <div class="legal-schedule-box">
            <div class="schedule-title">SCHEDULE A: CORE AGREED PROVISIONS</div>
            <table class="legal-terms-table">
                <thead>
                    <tr>
                        <th style="width: 18%;">Clause</th>
                        <th style="width: 82%;">Agreed Provision Details</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """

    # Optional Parties Header Callout
    parties_callout = ""
    if safe_parties:
        parties_callout = f"""
        <div class="legal-parties-banner">
            <span class="parties-label">PARTIES:</span> {safe_parties}
        </div>
        """

    full_document_html = f"""
    <div class="legalease-document-wrapper">
        <style>
            .legalease-document-wrapper {{
                background-color: #f8fafc;
                padding: 24px 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Georgia, serif;
                color: #1e293b;
                display: flex;
                justify-content: center;
            }}
            .legalease-paper {{
                background: #ffffff;
                width: 100%;
                max-width: 850px;
                padding: 48px 56px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
                box-sizing: border-box;
            }}
            .legal-draft-badge {{
                display: inline-block;
                background: #eef2ff;
                color: #4338ca;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                padding: 4px 10px;
                border-radius: 4px;
                border: 1px solid #c7d2fe;
                margin-bottom: 16px;
            }}
            .legal-doc-title {{
                font-size: 24px;
                font-weight: 800;
                color: #0f172a;
                text-align: center;
                letter-spacing: 0.02em;
                margin: 0 0 8px 0;
                line-height: 1.3;
            }}
            .legal-doc-date {{
                font-size: 14px;
                font-style: italic;
                color: #64748b;
                text-align: center;
                margin: 0 0 20px 0;
            }}
            .legal-doc-divider {{
                border: 0;
                height: 1px;
                background: #e2e8f0;
                margin: 20px 0;
            }}
            .legal-parties-banner {{
                background: #f1f5f9;
                border-left: 4px solid #3b82f6;
                padding: 10px 14px;
                font-size: 13px;
                color: #334155;
                border-radius: 0 6px 6px 0;
                margin-bottom: 24px;
                line-height: 1.5;
            }}
            .parties-label {{
                font-weight: 700;
                color: #1e293b;
            }}
            .legal-schedule-box {{
                margin: 24px 0;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                overflow: hidden;
            }}
            .schedule-title {{
                background: #f8fafc;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 700;
                color: #334155;
                letter-spacing: 0.05em;
                border-bottom: 1px solid #cbd5e1;
            }}
            .legal-terms-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }}
            .legal-terms-table th {{
                background: #f1f5f9;
                padding: 8px 14px;
                text-align: left;
                font-weight: 600;
                color: #0f172a;
                border-bottom: 1px solid #cbd5e1;
            }}
            .legal-terms-table td {{
                padding: 8px 14px;
                border-bottom: 1px solid #f1f5f9;
                color: #334155;
                line-height: 1.4;
            }}
            .term-col-num {{
                font-weight: 600;
                color: #2563eb;
                white-space: nowrap;
            }}
            .legal-h1 {{
                font-size: 18px;
                font-weight: 700;
                color: #0f172a;
                margin-top: 28px;
                margin-bottom: 10px;
                border-bottom: 1px solid #f1f5f9;
                padding-bottom: 4px;
            }}
            .legal-h2 {{
                font-size: 15px;
                font-weight: 700;
                color: #1e293b;
                margin-top: 20px;
                margin-bottom: 8px;
            }}
            .legal-h3 {{
                font-size: 14px;
                font-weight: 600;
                color: #334155;
                margin-top: 14px;
                margin-bottom: 6px;
            }}
            .legal-p {{
                font-size: 14px;
                line-height: 1.65;
                color: #334155;
                margin: 0 0 12px 0;
                text-align: justify;
            }}
            .legal-list {{
                margin: 0 0 14px 20px;
                padding: 0;
                font-size: 14px;
                line-height: 1.6;
                color: #334155;
            }}
            .legal-list li {{
                margin-bottom: 6px;
            }}
            .legal-signature-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 24px;
                margin-top: 36px;
                padding-top: 24px;
                border-top: 2px dashed #cbd5e1;
            }}
            .sig-party-block {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 16px;
            }}
            .sig-party-header {{
                font-size: 13px;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 16px;
            }}
            .sig-line-item {{
                font-size: 12px;
                color: #64748b;
                margin-bottom: 12px;
                border-bottom: 1px solid #cbd5e1;
                padding-bottom: 4px;
            }}
            .legal-disclaimer-card {{
                margin-top: 32px;
                padding: 14px 18px;
                background: #fffbeb;
                border: 1px solid #fef3c7;
                border-left: 4px solid #f59e0b;
                border-radius: 4px;
                font-size: 12px;
                color: #92400e;
                line-height: 1.5;
            }}
            .disclaimer-badge {{
                font-weight: 700;
                text-transform: uppercase;
                margin-right: 6px;
            }}
        </style>

        <div class="legalease-paper">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="legal-draft-badge">Formal Legal Draft</span>
                <span style="font-size: 11px; color: #94a3b8;">Generated via LegalEase AI</span>
            </div>

            <h1 class="legal-doc-title">{safe_title}</h1>
            {f'<div class="legal-doc-date">Effective Date: {safe_date}</div>' if safe_date else ''}
            <hr class="legal-doc-divider" />

            {parties_callout}
            {terms_table_html}

            <div class="legal-body-content">
                {body_html}
            </div>

            <div class="legal-signature-grid">
                <div class="sig-party-block">
                    <div class="sig-party-header">FIRST PARTY / DISCLOSING PARTY</div>
                    <div class="sig-line-item">Signature: ______________________________</div>
                    <div class="sig-line-item">Printed Name: ___________________________</div>
                    <div class="sig-line-item">Title: __________________________________</div>
                    <div class="sig-line-item">Date: ___________________________________</div>
                </div>
                <div class="sig-party-block">
                    <div class="sig-party-header">SECOND PARTY / RECEIVING PARTY</div>
                    <div class="sig-line-item">Signature: ______________________________</div>
                    <div class="sig-line-item">Printed Name: ___________________________</div>
                    <div class="sig-line-item">Title: __________________________________</div>
                    <div class="sig-line-item">Date: ___________________________________</div>
                </div>
            </div>

            <div class="legal-disclaimer-card">
                <span class="disclaimer-badge">Legal Notice:</span>
                LegalEase provides AI-generated legal drafting assistance for informational and starting purposes.
                It does not constitute formal legal representation or counsel. Always review with a qualified attorney in your governing jurisdiction before executing.
            </div>
        </div>
    </div>
    """
    return full_document_html


def _inline_markdown(text: str) -> str:
    """Helper to convert **bold** and *italic* markdown inline tags within HTML text."""
    # Bold **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # Italic *text* or _text_
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    return text
