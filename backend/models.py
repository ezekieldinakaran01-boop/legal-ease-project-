"""Pydantic models for LegalEase API validation and serialization."""

from datetime import datetime, date, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class DocumentGenerateRequest(BaseModel):
    """Request payload for generating a legal document."""
    document_type: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Type of legal document (e.g., NDA, Employment Contract, Lease Agreement)",
        examples=["Non-Disclosure Agreement (NDA)"]
    )
    parties: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Parties involved, their legal entity names, addresses, and defined roles",
        examples=["Party A: Alpha Corp (Disclosing Party), 123 Tech Blvd; Party B: Beta LLC (Receiving Party), 456 Innovation Way"]
    )
    terms: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Key terms, covenants, and clauses, separated by semicolons or newlines",
        examples=["Confidentiality period lasts 3 years; Permitted use is evaluation only; Return of materials upon 10 days notice"]
    )
    effective_date: str = Field(
        ...,
        min_length=4,
        max_length=50,
        description="Effective date of the document (e.g., YYYY-MM-DD or Month DD, YYYY)",
        examples=["2026-10-01"]
    )
    additional_instructions: Optional[str] = Field(
        default="",
        max_length=3000,
        description="Optional additional instructions, specific jurisdictional context, or custom clauses"
    )

    @field_validator("document_type", "parties", "terms", "effective_date")
    @classmethod
    def validate_non_empty_whitespace(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' must not be empty or solely whitespace.")
        return stripped

    @field_validator("additional_instructions")
    @classmethod
    def clean_additional_instructions(cls, v: Optional[str]) -> str:
        return (v or "").strip()


class DocumentGenerateResponse(BaseModel):
    """Response payload returned upon successful legal document generation."""
    success: bool = True
    document_type: str
    content: str
    effective_date: Optional[str] = None
    parties: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    word_count: int = 0
    char_count: int = 0
    terms_count: int = 0
    disclaimer: str = (
        "LegalEase provides AI-generated legal information and drafting assistance. "
        "It is not a substitute for advice from a qualified legal professional. "
        "Review documents for your jurisdiction and circumstances before using them."
    )


class DocumentExportRequest(BaseModel):
    """Request payload for exporting a document to DOCX, PDF, or TXT."""
    document_type: str = Field(..., min_length=2, description="Document title/type")
    content: str = Field(..., min_length=5, description="Full legal document text")
    effective_date: Optional[str] = Field(default="", description="Effective date")
    parties: Optional[str] = Field(default="", description="Parties string")
    terms: Optional[str] = Field(default="", description="Key terms")
    logo_base64: Optional[str] = Field(
        default=None,
        description="Optional base64 encoded PNG/JPEG image for document header branding"
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Document content to export cannot be empty.")
        return stripped


class HealthResponse(BaseModel):
    """Health check status response."""
    status: str = "healthy"
    service: str = "LegalEase Backend API"
    version: str = "1.0.0"
    ai_model: str
    gemini_configured: bool
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ServiceInfoResponse(BaseModel):
    """Root info endpoint response."""
    name: str = "LegalEase – AI-Powered Legal Document Generator"
    version: str = "1.0.0"
    status: str = "running"
    description: str = "Enterprise AI platform for generating, reviewing, and exporting production-quality legal documents."
    disclaimer: str = (
        "LegalEase provides AI-generated legal information and drafting assistance. "
        "It is not a substitute for advice from a qualified legal professional."
    )
    endpoints: dict = Field(
        default_factory=lambda: {
            "GET /": "Service overview & documentation link",
            "GET /health": "System health & AI configuration check",
            "POST /generate": "Generate structured legal document using Google Gemini",
            "POST /export/docx": "Export document to Microsoft Word format",
            "POST /export/pdf": "Export document to PDF format",
            "POST /export/txt": "Export document to clean Plain Text format"
        }
    )
