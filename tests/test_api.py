"""Unit and integration tests for FastAPI backend endpoints."""

import os
import sys
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.main import app
from ai_core.gemini_generator import GeminiGenerationError

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint returns service info and active status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "LegalEase" in data["name"]
    assert "endpoints" in data
    assert "POST /generate" in data["endpoints"]


def test_health_endpoint():
    """Verify that health check returns healthy status and model configuration."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ai_model" in data
    assert "gemini_configured" in data


def test_generate_validation_missing_fields():
    """Verify that omitting required fields returns HTTP 422 validation error."""
    # Missing parties and terms
    payload = {
        "document_type": "Non-Disclosure Agreement (NDA)",
        "effective_date": "2026-10-01",
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422


def test_generate_validation_empty_whitespace_fields():
    """Verify that whitespace-only fields are rejected by Pydantic validators."""
    payload = {
        "document_type": "NDA",
        "parties": "   ",
        "terms": "   ",
        "effective_date": "2026-10-01",
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422


@patch("backend.routes.ai_generator.generate_document")
def test_generate_successful_with_mocked_gemini(mock_generate):
    """Verify successful document generation when Gemini responds properly."""
    mock_content = (
        "NON-DISCLOSURE AGREEMENT\n\n"
        "SECTION 1. CONFIDENTIAL INFORMATION\n"
        "The receiving party agrees to maintain strict confidentiality.\n\n"
        "IN WITNESS WHEREOF, the parties execute this agreement."
    )
    mock_generate.return_value = {
        "content": mock_content,
        "document_type": "Non-Disclosure Agreement (NDA)",
        "model_used": "gemini-2.5-flash",
        "backend_used": "google-genai",
        "word_count": len(mock_content.split()),
        "char_count": len(mock_content),
    }

    payload = {
        "document_type": "Non-Disclosure Agreement (NDA)",
        "parties": "Party A: Acme Inc; Party B: Beta Corp",
        "terms": "Confidentiality lasts 3 years; Permitted use is evaluation only",
        "effective_date": "2026-10-01",
        "additional_instructions": "Delaware law",
    }

    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["document_type"] == "Non-Disclosure Agreement (NDA)"
    assert "CONFIDENTIAL INFORMATION" in data["content"]
    assert data["word_count"] > 0
    assert "LegalEase provides AI-generated" in data["disclaimer"]


@patch("backend.routes.ai_generator.generate_document")
def test_generate_gemini_error_handling(mock_generate):
    """Verify that GeminiGenerationError returns a friendly HTTP 500 error."""
    mock_generate.side_effect = GeminiGenerationError("API key quota exceeded or invalid key.")

    payload = {
        "document_type": "Service Agreement",
        "parties": "Provider: ABC LLC; Client: XYZ Inc",
        "terms": "Monthly retainer of $5,000; Net 30 payment terms",
        "effective_date": "2026-11-01",
    }

    response = client.post("/generate", json=payload)
    assert response.status_code == 500
    assert "API key quota exceeded" in response.json()["detail"]


def test_export_txt_endpoint():
    """Verify backend TXT export endpoint."""
    payload = {
        "document_type": "Test Agreement",
        "content": "SECTION 1. SCOPE OF SERVICES\nProvider shall deliver consulting services.",
        "effective_date": "2026-10-01",
        "parties": "Alpha Corp and Beta LLC",
        "terms": "Term 1; Term 2",
    }
    response = client.post("/export/txt", json=payload)
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "TEST AGREEMENT" in response.text


def test_export_docx_endpoint():
    """Verify backend DOCX export endpoint produces valid Word binary."""
    payload = {
        "document_type": "Master Services Agreement",
        "content": "ARTICLE I. DEFINITIONS\nCapitalized terms shall have defined meanings.",
        "effective_date": "2026-10-01",
        "parties": "Party A and Party B",
        "terms": "Payment net 30; Mutual indemnification",
    }
    response = client.post("/export/docx", json=payload)
    assert response.status_code == 200
    assert "openxmlformats" in response.headers["content-type"]
    assert len(response.content) > 1000  # Non-empty docx file


def test_export_pdf_endpoint():
    """Verify backend PDF export endpoint produces valid PDF binary."""
    payload = {
        "document_type": "Consulting Agreement",
        "content": "SECTION 1. DELIVERABLES\nConsultant shall deliver weekly reports.",
        "effective_date": "2026-10-01",
        "parties": "Party A and Party B",
        "terms": "Rate of $150/hr; Termination with 7 days notice",
    }
    response = client.post("/export/pdf", json=payload)
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]
    assert response.content.startswith(b"%PDF")
