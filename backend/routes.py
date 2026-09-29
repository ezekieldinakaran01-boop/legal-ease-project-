"""FastAPI route handlers for LegalEase API."""

import base64
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from .models import (
    DocumentGenerateRequest,
    DocumentGenerateResponse,
    DocumentExportRequest,
    HealthResponse,
    ServiceInfoResponse,
)
from ai_core.gemini_generator import GeminiDocumentGenerator, GeminiGenerationError
from document_utils.sanitizer import parse_terms_list
from document_utils.docx_generator import generate_docx
from document_utils.pdf_generator import generate_pdf
from document_utils.txt_generator import generate_txt

logger = logging.getLogger("legalease.routes")

router = APIRouter()
ai_generator = GeminiDocumentGenerator()


@router.get("/", response_model=ServiceInfoResponse, summary="Service Information")
def get_service_info():
    """Return platform metadata, health status, and available API endpoints."""
    return ServiceInfoResponse()


@router.get("/health", response_model=HealthResponse, summary="Health Check")
def get_health():
    """Check backend service liveness and Gemini AI configuration status."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ai_model=ai_generator.model_name,
        gemini_configured=ai_generator.is_configured(),
    )


@router.post(
    "/generate",
    response_model=DocumentGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Legal Document",
)
def generate_document(request: DocumentGenerateRequest):
    """Generate a formal, structured legal document using Google Gemini."""
    try:
        logger.info("Received generation request for document type: %s", request.document_type)

        result = ai_generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
            additional_instructions=request.additional_instructions,
        )

        parsed_terms = parse_terms_list(request.terms)

        return DocumentGenerateResponse(
            success=True,
            document_type=request.document_type,
            content=result["content"],
            effective_date=request.effective_date,
            parties=request.parties,
            word_count=result.get("word_count", 0),
            char_count=result.get("char_count", 0),
            terms_count=len(parsed_terms),
        )

    except GeminiGenerationError as e:
        logger.error("Gemini generation error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Unexpected error during document generation: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the document. Please verify your inputs and try again.",
        )


@router.post("/export/docx", summary="Export Document to DOCX")
def export_docx(request: DocumentExportRequest):
    """Generate and return a professionally formatted Microsoft Word (.docx) document."""
    try:
        terms_list = parse_terms_list(request.terms) if request.terms else []
        logo_bytes = None
        if request.logo_base64:
            try:
                logo_bytes = base64.b64decode(request.logo_base64)
            except Exception:
                logger.warning("Failed to decode base64 logo in export_docx request")

        docx_buffer = generate_docx(
            document_text=request.content,
            document_title=request.document_type,
            effective_date=request.effective_date,
            parties=request.parties,
            terms_list=terms_list,
            logo_bytes=logo_bytes,
        )

        filename = f"{request.document_type.replace(' ', '_')}.docx"
        return Response(
            content=docx_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.exception("DOCX export error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX document: {str(e)}",
        )


@router.post("/export/pdf", summary="Export Document to PDF")
def export_pdf(request: DocumentExportRequest):
    """Generate and return a publication-grade PDF legal document."""
    try:
        terms_list = parse_terms_list(request.terms) if request.terms else []
        logo_bytes = None
        if request.logo_base64:
            try:
                logo_bytes = base64.b64decode(request.logo_base64)
            except Exception:
                logger.warning("Failed to decode base64 logo in export_pdf request")

        pdf_buffer = generate_pdf(
            document_text=request.content,
            document_title=request.document_type,
            effective_date=request.effective_date,
            parties=request.parties,
            terms_list=terms_list,
            logo_bytes=logo_bytes,
        )

        filename = f"{request.document_type.replace(' ', '_')}.pdf"
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.exception("PDF export error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF document: {str(e)}",
        )


@router.post("/export/txt", summary="Export Document to TXT")
def export_txt(request: DocumentExportRequest):
    """Generate and return a clean ASCII Plain Text legal document."""
    try:
        terms_list = parse_terms_list(request.terms) if request.terms else []
        txt_content = generate_txt(
            document_text=request.content,
            document_title=request.document_type,
            effective_date=request.effective_date,
            parties=request.parties,
            terms_list=terms_list,
        )

        filename = f"{request.document_type.replace(' ', '_')}.txt"
        return Response(
            content=txt_content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.exception("TXT export error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate TXT document: {str(e)}",
        )
