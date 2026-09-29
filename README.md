# ⚖️ LegalEase – AI-Powered Legal Document Generator

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B.svg?logo=streamlit)](https://streamlit.io)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20SDK-4285F4.svg?logo=google)](https://aistudio.google.com/)
[![Tests](https://img.shields.io/badge/tests-18%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**LegalEase** is a production-grade, full-stack LegalTech web application that transforms contract terms, party covenants, and jurisdictional specifications into publication-grade legal documents in seconds. Powered by Google Gemini AI, LegalEase combines formal contract drafting algorithms with an interactive editor and multi-format document compilers for **Microsoft Word (DOCX)**, **PDF**, and **Plain Text (TXT)**.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture & System Flow](#-architecture--system-flow)
- [Project Directory Structure](#-project-directory-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start & Installation](#-quick-start--installation)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Supported Document Types & Templates](#-supported-document-types--templates)
- [Document Export Specifications](#-document-export-specifications)
- [Testing Suite](#-testing-suite)
- [Docker & Production Deployment](#-docker--production-deployment)
- [Security & Privacy](#-security--privacy)
- [Legal Safety & Disclaimer](#-legal-safety--disclaimer)

---

## 🌟 Key Features

- **Jurisdiction-Aware AI Drafting**: Uses Google Gemini (`gemini-2.5-flash` / configurable) to generate comprehensive legal agreements with formal recitals, defined terms, operative covenants, representations, warranties, indemnities, and execution blocks.
- **Interactive Document Editor**: Switch between a high-fidelity formatted legal brief preview and a live inline text editor with word/character telemetry. Any user modifications are immediately preserved in all exports.
- **Multi-Format Export Pipelines**:
  - **Microsoft Word (.docx)**: Clean 1-inch margins, Times New Roman typography, shaded Schedule tables, dual-column signature execution blocks, and running headers/footers via `python-docx`.
  - **Publication-Grade PDF**: Formatted via `fpdf2` with running headers, dynamic page numbering (`Page X of Y`), clean table wrapping, and dual-party signature blocks.
  - **Plain Text (.txt)**: Clean ASCII format with section headers and border dividers for archival and email use.
- **Custom Branding Support**: Upload firm or corporate logos (PNG, JPG, max 2.5MB) to automatically embed high-resolution branding into DOCX and PDF document headers.
- **Pre-Configured Legal Templates**: One-click loaders for NDAs, Freelance Agreements, Employment Offer Letters, Residential Leases, and Service Level Agreements.
- **Enterprise Security**: Zero hardcoded credentials, full XSS sanitization, image verification via Pillow, and strict Pydantic input validation.

---

## 🏛️ Architecture & System Flow

```
                      ┌───────────────────────────────────────┐
                      │          Browser / End User           │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │       Streamlit SaaS UI (:8501)       │
                      │  • Dashboard & Template Loader        │
                      │  • Interactive Clause Editor          │
                      │  • Formatted Brief HTML Preview       │
                      └──────────────────┬────────────────────┘
                                         │ (HTTP JSON REST)
                                         ▼
                      ┌───────────────────────────────────────┐
                      │       FastAPI ASGI API (:8000)        │
                      │  • Request Validation (Pydantic)      │
                      │  • Health & Telemetry Endpoints       │
                      │  • Document Generation & Export API   │
                      └─────────┬───────────────────┬─────────┘
                                │                   │
            (AI Prompt Engineering)       (Document Compilation)
                                │                   │
                                ▼                   ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│     Google Gemini AI Core       │   │     Document Utilities          │
│ • google-genai / SDK fallback   │   │ • docx_generator (python-docx)  │
│ • Structured Legal Schema       │   │ • pdf_generator (fpdf2)         │
│ • Zero hallucination restraints │   │ • txt_generator & sanitizer     │
└─────────────────────────────────┘   └─────────────────────────────────┘
```

---

## 📁 Project Directory Structure

```
LegalEase/
├── backend/
│   ├── __init__.py                # Backend module initialization
│   ├── main.py                    # FastAPI server entrypoint & CORS middleware
│   ├── routes.py                  # API route handlers (/generate, /health, /export/*)
│   └── models.py                  # Pydantic validation schemas
│
├── ai_core/
│   ├── __init__.py                # AI module exports
│   └── gemini_generator.py        # Gemini SDK wrapper with prompt engineering
│
├── document_utils/
│   ├── __init__.py                # Document compilation utilities
│   ├── docx_generator.py          # Microsoft Word (.docx) generator
│   ├── pdf_generator.py           # Publication-grade PDF generator
│   ├── txt_generator.py           # Plain text (.txt) generator
│   ├── html_preview.py            # Sanitized legal brief HTML renderer
│   └── sanitizer.py               # Unicode normalization & XSS sanitizer
│
├── frontend/
│   └── app.py                     # Streamlit SaaS web application
│
├── assets/
│   └── logo.png                   # LegalEase brand logo asset
│
├── tests/
│   ├── __init__.py                # Test package initialization
│   ├── test_api.py                # FastAPI endpoints & validation tests
│   └── test_document_generation.py# Unit tests for DOCX, PDF, TXT, and sanitizer
│
├── .env.example                   # Template for environment variables
├── .gitignore                     # Git exclusion rules for secrets and virtualenvs
├── requirements.txt               # Production Python dependencies
├── Dockerfile                     # Multi-service container specification
└── README.md                      # Comprehensive project documentation
```

---

## 🔧 Prerequisites

- **Python**: Version `3.10` or higher (`Python 3.12` recommended)
- **Google Gemini API Key**: Free or paid key from [Google AI Studio](https://aistudio.google.com/)
- **Operating System**: Windows, macOS, or Linux

---

## 🚀 Quick Start & Installation

### 1. Clone or Navigate to the Repository

```bash
cd LegalEase
```

### 2. Create and Activate a Virtual Environment

On **Windows (PowerShell)**:
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

On **macOS / Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and set your credentials:

```ini
# Google Gemini API Key (Obtain from https://aistudio.google.com/)
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere

# Model configuration (Defaults to gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Backend API settings
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_URL=http://127.0.0.1:8000

# Environment mode
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 🖥️ Running the Application

LegalEase is structured as a full-stack system with a **FastAPI backend** and a **Streamlit frontend**. You can start both services in separate terminal windows.

### Terminal 1: Launch FastAPI Backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
- API will be accessible at: `http://127.0.0.1:8000`
- Interactive OpenAPI Swagger documentation: `http://127.0.0.1:8000/docs`
- ReDoc documentation: `http://127.0.0.1:8000/redoc`

### Terminal 2: Launch Streamlit Frontend

```bash
streamlit run frontend/app.py
```
- Web application will automatically open in your default browser at: `http://localhost:8501`

*(Note: The Streamlit frontend includes automatic failover to direct AI generation if the FastAPI backend is temporarily stopped, ensuring uninterrupted workflow.)*

---

## 📡 API Documentation

### 1. Service Health Check

`GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "LegalEase Backend API",
  "version": "1.0.0",
  "ai_model": "gemini-2.5-flash",
  "gemini_configured": true,
  "timestamp": "2026-09-28T09:30:00Z"
}
```

### 2. Generate Legal Document

`POST /generate`

**Request Body:**
```json
{
  "document_type": "Non-Disclosure Agreement (NDA)",
  "parties": "Party A: Apex Inc (Disclosing Party), 500 Tech Blvd, SF; Party B: Quantum LLC (Receiving Party), 120 Wall St, NYC",
  "terms": "Confidentiality duration is 3 years; Permitted use is evaluation only; Return materials within 10 days notice",
  "effective_date": "2026-10-01",
  "additional_instructions": "Governing law: Delaware. Standard injunctive relief clause."
}
```

**Response Body:**
```json
{
  "success": true,
  "document_type": "Non-Disclosure Agreement (NDA)",
  "content": "MUTUAL NON-DISCLOSURE AGREEMENT\n\nThis Mutual Non-Disclosure Agreement...",
  "effective_date": "2026-10-01",
  "parties": "Party A: Apex Inc...",
  "word_count": 842,
  "char_count": 5610,
  "terms_count": 3,
  "disclaimer": "LegalEase provides AI-generated legal information and drafting assistance..."
}
```

### 3. Export Endpoints

- `POST /export/docx` -> Downloads compiled `.docx` Word binary.
- `POST /export/pdf` -> Downloads compiled `.pdf` document binary.
- `POST /export/txt` -> Downloads clean ASCII `.txt` document.

---

## 📑 Supported Document Types & Templates

LegalEase supports out-of-the-box generation for standard commercial and legal instruments:

1. **Non-Disclosure Agreement (NDA)**: Unilateral and mutual confidentiality covenants, definitions of proprietary information, trade secret safeguards, and non-circumvention.
2. **Contract / General Commercial Agreement**: Broad bilateral obligations, representations, warranties, and force majeure clauses.
3. **Employment Contract**: Full-time terms, duties, intellectual property assignment, non-solicitation, and severance terms.
4. **Employment Offer Letter**: Executive & staff offer terms, compensation, bonus structure, stock option vesting schedules, and contingencies.
5. **Lease Agreement**: Residential and commercial real property leases, rent terms, security deposits, maintenance obligations, and default remedies.
6. **Freelance / Contractor Agreement**: Statement of work milestones, fee schedules, independent contractor tax classification, and work-for-hire copyright assignment.
7. **Service Agreement (SLA)**: Managed service deliverables, uptime SLAs, recurring billing, indemnification, and liability caps.
8. **Custom Document Type**: Free-form drafting for unique commercial instruments.

---

## 🧪 Testing Suite

LegalEase includes comprehensive unit and integration tests using `pytest` and FastAPI's `TestClient`.

### Running All Tests

```bash
pytest tests/ -v
```

### Test Coverage Highlights:
- **API Endpoints**: Validates `/`, `/health`, and `/generate` with both valid inputs and whitespace/missing field edge cases.
- **Mocked AI Generation**: Simulates Gemini AI responses without consuming API quota or requiring a live key.
- **Export Pipelines**: Tests DOCX, PDF, and TXT binary generation and verifies that magic bytes (`PK\x03\x04` for Word, `%PDF` for PDF) and structure are intact.
- **XSS & Security**: Tests regex sanitizers against `<script>`, `<iframe>`, and malicious `javascript:` schemes.
- **Logo Embeddings**: Verifies in-memory PIL byte handling for document headers.

---

## 🐳 Docker & Production Deployment

### Building the Docker Container

```bash
docker build -t legalease:latest .
```

### Running the Container

```bash
docker run -d \
  -p 8000:8000 \
  -p 8501:8501 \
  -e GEMINI_API_KEY="your_api_key_here" \
  -e GEMINI_MODEL="gemini-2.5-flash" \
  --name legalease-app \
  legalease:latest
```

The container starts both the FastAPI backend and Streamlit frontend concurrently.

---

## 🔒 Security & Privacy

- **Zero API Key Leakage**: API credentials are read strictly from local `.env` files or container environment variables. Keys are never logged or exposed in HTTP responses.
- **Strict File Upload Controls**: File uploads are restricted to `.png`, `.jpg`, `.jpeg` and capped at 2.5MB. Images are verified using Pillow to guard against payload polyglots.
- **XSS Sanitization**: User inputs and generated legal markdown are passed through a custom sanitization pipeline before HTML preview rendering.
- **Confidentiality**: Contractual terms and party names are transmitted securely directly to the Google Gemini API over TLS and are never stored in telemetry or databases.

---

## ⚖️ Legal Safety & Disclaimer

> [!IMPORTANT]
> **LegalEase provides AI-generated legal information and drafting assistance. It is not a substitute for advice from a qualified legal professional.**
>
> Laws, regulations, and judicial interpretations vary significantly across jurisdictions (local, state, federal, and international). Documents produced by LegalEase are intended solely as starting drafts. Users must have all agreements reviewed, customized, and approved by a licensed attorney authorized to practice in their governing jurisdiction prior to execution.
