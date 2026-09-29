"""Text, HTML, and term sanitization utilities for LegalEase."""

import re
import html
from typing import List


def clean_text_for_document(text: str) -> str:
    """Normalize unicode quotes, dashes, bullets, and whitespace for DOCX and PDF export.

    This ensures that characters outside standard ASCII/Latin-1 do not cause font encoding
    crashes in PDF generators while preserving professional typography in output.
    """
    if not text:
        return ""

    replacements = {
        "\u2018": "'",  # Left single quote
        "\u2019": "'",  # Right single quote
        "\u201c": '"',  # Left double quote
        "\u201d": '"',  # Right double quote
        "\u2014": " -- ",  # Em dash
        "\u2013": " - ",  # En dash
        "\u2026": "...",  # Ellipsis
        "\u00a0": " ",  # Non-breaking space
        "\u2022": "*",  # Bullet
        "\u25cf": "*",  # Black circle bullet
        "\u25aa": "*",  # Black small square bullet
        "\u2010": "-",  # Hyphen
        "\u2011": "-",  # Non-breaking hyphen
        "\u2032": "'",  # Prime
        "\u2033": '"',  # Double prime
        "\t": "    ",  # Replace tabs with 4 spaces
    }

    cleaned = text
    for original, replacement in replacements.items():
        cleaned = cleaned.replace(original, replacement)

    # Normalize carriage returns and newlines
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Remove non-printable control characters except newline
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    return cleaned


def sanitize_html(content: str) -> str:
    """Sanitize content to prevent XSS attacks while preserving structured legal presentation.

    Escapes script, iframe, object, embed tags, and event handlers like onclick/onload.
    """
    if not content:
        return ""

    # First disarm any direct script, iframe, style, or link tags
    dangerous_tags_pattern = re.compile(
        r"<\s*(script|style|iframe|object|embed|applet|meta|form|input|button|svg|base)\b[^>]*>.*?</\s*\1\s*>",
        re.IGNORECASE | re.DOTALL
    )
    sanitized = dangerous_tags_pattern.sub("", content)

    # Disarm self-closing or unclosed dangerous tags
    sanitized = re.sub(r"<\s*(script|style|iframe|object|embed|applet|meta|form|input|button|svg|base)\b[^>]*>", "", sanitized, flags=re.IGNORECASE)

    # Disarm dangerous event handlers like onclick="...", onload="...", etc.
    sanitized = re.sub(r"\bon\w+\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)", "", sanitized, flags=re.IGNORECASE)

    # Disarm javascript: pseudo-protocol in href or src
    sanitized = re.sub(r"(href|src)\s*=\s*['\"]?\s*javascript:[^'\">]*['\"]?", "", sanitized, flags=re.IGNORECASE)

    return sanitized


def parse_terms_list(terms_str: str) -> List[str]:
    """Parse user terms and conditions into a clean list of individual provisions.

    Supports inputs separated by semicolons (;) or newlines.
    Strips leading bullet characters and numbers.
    """
    if not terms_str:
        return []

    # If semicolons are present, prioritize semicolon separation; otherwise use newlines
    if ";" in terms_str:
        raw_items = terms_str.split(";")
    else:
        raw_items = terms_str.split("\n")

    cleaned_terms: List[str] = []
    for item in raw_items:
        t = item.strip()
        # Strip common leading bullet marks or numbers like "1. ", "* ", "- "
        t = re.sub(r"^(\d+[\.\)]|[-*•]\s*)\s*", "", t)
        t = t.strip()
        if t and len(t) > 2:
            cleaned_terms.append(t)

    return cleaned_terms
