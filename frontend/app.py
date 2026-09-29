"""LegalEase – AI-Powered Legal Document Generator
Streamlit SaaS Frontend Application.
"""

import os
import sys
import io
import json
import base64
from datetime import date, datetime
import requests
import streamlit as st
from PIL import Image

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from document_utils.sanitizer import parse_terms_list, clean_text_for_document
from document_utils.html_preview import convert_markdown_to_legal_html
from document_utils.docx_generator import generate_docx
from document_utils.pdf_generator import generate_pdf
from document_utils.txt_generator import generate_txt
from ai_core.gemini_generator import GeminiDocumentGenerator, GeminiGenerationError

# ---------------------------------------------------------
# Streamlit App Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="LegalEase – AI Legal Document Generator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom SaaS CSS Theme
SAAS_CSS = """
<style>
    /* Global Typography & Palette */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Hero Header */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 12px;
        padding: 28px 36px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #334155;
    }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-tagline {
        font-size: 14px;
        color: #94a3b8;
        max-width: 680px;
        line-height: 1.5;
        margin: 0;
    }

    /* Feature Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .step-number {
        display: inline-block;
        width: 26px;
        height: 26px;
        line-height: 26px;
        text-align: center;
        background: #eff6ff;
        color: #2563eb;
        font-size: 12px;
        font-weight: 700;
        border-radius: 50%;
        margin-bottom: 8px;
    }
    .step-title {
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .step-desc {
        font-size: 13px;
        color: #64748b;
        line-height: 1.4;
    }

    /* Legal Disclaimer Banner */
    .legal-alert {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        border-top: 1px solid #fef3c7;
        border-right: 1px solid #fef3c7;
        border-bottom: 1px solid #fef3c7;
        padding: 12px 16px;
        border-radius: 6px;
        font-size: 12.5px;
        color: #92400e;
        line-height: 1.5;
        margin-bottom: 20px;
    }

    /* Status Pill */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11.5px;
        font-weight: 600;
    }
    .status-active {
        background-color: #dcfce7;
        color: #15803d;
    }
    .status-warning {
        background-color: #fef3c7;
        color: #b45309;
    }

    /* Document Type Pill Badges */
    .badge-pill {
        display: inline-block;
        background: #f1f5f9;
        color: #334155;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        margin: 2px 4px 2px 0;
        border: 1px solid #e2e8f0;
    }
</style>
"""
st.markdown(SAAS_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# Backend URL Configuration & Session State Setup
# ---------------------------------------------------------
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
BACKEND_URL = os.getenv("BACKEND_URL", f"http://{BACKEND_HOST}:{BACKEND_PORT}")

# Initialize Session States
if "generated_document" not in st.session_state:
    st.session_state["generated_document"] = None
if "document_type" not in st.session_state:
    st.session_state["document_type"] = "Non-Disclosure Agreement (NDA)"
if "parties" not in st.session_state:
    st.session_state["parties"] = ""
if "terms" not in st.session_state:
    st.session_state["terms"] = ""
if "effective_date" not in st.session_state:
    st.session_state["effective_date"] = date.today()
if "additional_instructions" not in st.session_state:
    st.session_state["additional_instructions"] = ""
if "terms_list" not in st.session_state:
    st.session_state["terms_list"] = []
if "uploaded_logo_bytes" not in st.session_state:
    st.session_state["uploaded_logo_bytes"] = None
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Formatted Document Preview"
if "generation_metadata" not in st.session_state:
    st.session_state["generation_metadata"] = None

# Sample Templates Catalog
SAMPLE_TEMPLATES = {
    "Non-Disclosure Agreement (NDA)": {
        "parties": "Disclosing Party: Apex Innovations Inc., 500 Tech Boulevard, Suite 400, San Francisco, CA 94107;\nReceiving Party: Quantum Analytics LLC, 120 Wall Street, 22nd Floor, New York, NY 10005",
        "terms": "Confidential Information encompasses all proprietary software source code, system architectures, customer lists, and financial records;\nReceiving Party shall preserve confidentiality and refrain from unauthorized disclosure for a period of three (3) years;\nPermitted use is strictly limited to evaluating a prospective commercial partnership;\nStandard exclusions apply to publicly known data or independently developed information;\nAll confidential materials and copies must be returned or certified destroyed within ten (10) business days of written notice.",
        "additional_instructions": "Governing law shall be the State of Delaware. Include provisions for standard injunctive relief in case of breach.",
    },
    "Freelance / Contractor Agreement": {
        "parties": "Client: BrightWave Digital Media LLC, 742 Evergreen Terrace, Seattle, WA 98101;\nContractor: Jane Doe, d/b/a Studio Doe Design, 101 Creative Way, Austin, TX 78701",
        "terms": "Contractor shall deliver complete brand identity guidelines and responsive UI component mockups by November 15, 2026;\nTotal fixed fee compensation is $8,500 USD, payable 50% upon execution and 50% upon final milestone acceptance;\nInvoices are payable net 15 calendar days from submission;\nAll proprietary work product, copyrights, and intellectual property vest solely in Client upon full settlement of compensation;\nEither party may terminate without cause upon fourteen (14) calendar days advance written notice.",
        "additional_instructions": "Specify independent contractor status with no employment benefits. Include standard confidentiality covenants.",
    },
    "Employment Offer Letter": {
        "parties": "Employer: CloudScale Systems Inc., 800 Market Street, San Francisco, CA 94102;\nCandidate: Alex Mercer, 245 Pine Street, Oakland, CA 94612",
        "terms": "Position Title: Senior Backend Systems Engineer reporting to the VP of Engineering;\nAnnual Base Salary of $165,000 USD paid in semi-monthly installments;\nEligibility for an annual target performance bonus of 15% subject to company and individual goals;\nOption grant to purchase 25,000 shares of Common Stock subject to standard 4-year vesting with a 1-year cliff;\nComprehensive medical, dental, vision coverage, and 401(k) retirement plan with 4% employer matching;\nEmployment relationship is at-will and contingent upon satisfactory background verification.",
        "additional_instructions": "Offer valid for acceptance until October 15, 2026. Anticipated start date is November 1, 2026.",
    },
    "Residential Lease Agreement": {
        "parties": "Landlord: Maple Leaf Property Management LLC, 100 Oakwood Drive, Denver, CO 80203;\nTenants: Jordan Smith and Taylor Smith, currently residing at 55 Elm Street, Denver, CO 80205",
        "terms": "Leased premises situated at 1420 Silverlake Boulevard, Apartment 304, Denver, CO 80202;\nLease term duration is twelve (12) calendar months starting on the Effective Date;\nMonthly base rent of $2,400 USD payable in advance on or before the first day of each month;\nRefundable security deposit of $2,400 USD deposited into a designated trust account;\nA late fee of $75 USD applies to rent received after the 5th day of the month;\nStrict no unauthorized pets policy without prior written consent and executed pet addendum;\nTenants responsible for gas, electricity, and internet utility services.",
        "additional_instructions": "Governing jurisdiction: State of Colorado. Landlord requires 24 hours notice for property inspection.",
    },
    "Service Agreement": {
        "parties": "Provider: Apex Cloud Hosting Solutions LLC, 900 Server Lane, Dallas, TX 75201;\nCustomer: OmniRetail Enterprise Corp., 450 Commerce Square, Chicago, IL 60601",
        "terms": "Provider agrees to supply managed cloud hosting infrastructure with 99.95% monthly uptime service level guarantee (SLA);\nCustomer shall pay a recurring monthly fee of $3,200 USD due on the 1st of each billing cycle;\nService credits of 5% of monthly fee allocated for every 30 minutes of unscheduled downtime exceeding SLA;\nMutual indemnification for third-party intellectual property infringement claims;\nInitial service contract term of 24 months with automatic renewal unless terminated with 30 days notice.",
        "additional_instructions": "Governing law: State of Texas. Include standard limitation of liability capped at fees paid over preceding 12 months.",
    },
}

DOCUMENT_TYPE_CHOICES = [
    "General Agreement",
    "Contract",
    "Non-Disclosure Agreement (NDA)",
    "Lease Agreement",
    "Employment Contract",
    "Employment Offer Letter",
    "Freelance Agreement",
    "Service Agreement",
    "Custom Document Type",
]


def check_backend_health():
    """Verify backend connectivity and Gemini status."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2.5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


# ---------------------------------------------------------
# Sidebar Layout & Navigation
# ---------------------------------------------------------
with st.sidebar:
    # App Branding
    logo_path = os.path.join(project_root, "assets", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("## ⚖️ **LegalEase**")

    st.caption("AI-Powered Legal Drafting Platform")
    st.divider()

    # Navigation Menu
    menu_choice = st.radio(
        "Navigation",
        options=["📊 Dashboard", "✍️ Create Document", "📄 Document Preview", "ℹ️ About & Legal"],
        index=0 if st.session_state["generated_document"] is None else 2,
    )

    st.divider()

    # Backend & AI Health Status Card
    st.markdown("##### 🔌 **System Status**")
    backend_info = check_backend_health()
    if backend_info:
        st.markdown(
            '<div class="status-pill status-active">● Backend API Connected</div>',
            unsafe_allow_html=True,
        )
        model_str = backend_info.get("ai_model", "gemini-2.5-flash")
        gemini_ok = backend_info.get("gemini_configured", False)
        if gemini_ok:
            st.markdown(
                f'<div class="status-pill status-active" style="margin-top:4px;">● AI Engine Ready ({model_str})</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-pill status-warning" style="margin-top:4px;">▲ GEMINI_API_KEY Missing in .env</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="status-pill status-warning">▲ Backend Offline (Direct Mode Active)</div>',
            unsafe_allow_html=True,
        )
        # Direct check
        direct_gen = GeminiDocumentGenerator()
        if direct_gen.is_configured():
            st.markdown(
                f'<div class="status-pill status-active" style="margin-top:4px;">● Direct AI Ready ({direct_gen.model_name})</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-pill status-warning" style="margin-top:4px;">▲ Set GEMINI_API_KEY in .env</div>',
                unsafe_allow_html=True,
            )

    st.caption("Backend URL: " + BACKEND_URL)
    st.divider()

    st.markdown("##### 💡 **Quick Tips**")
    st.markdown(
        "- Separate distinct terms with **semicolons (`;`)**\n"
        "- Use the **Sample Templates** to auto-fill realistic clauses\n"
        "- Modify draft text in **Edit Mode** before exporting\n"
        "- Export with one click to **DOCX**, **PDF**, or **TXT**"
    )


# ---------------------------------------------------------
# Page 1: Dashboard
# ---------------------------------------------------------
if menu_choice == "📊 Dashboard":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">⚖️ LegalEase Platform</div>
            <p class="hero-tagline">
                Transform complex commercial agreements and legal contracts into structured,
                lawyer-grade drafts in seconds using Google Gemini AI and multi-format document compilers.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mandatory Legal Notice
    st.markdown(
        """
        <div class="legal-alert">
            <strong>IMPORTANT LEGAL NOTICE:</strong> LegalEase provides AI-generated legal information and drafting assistance.
            It is not a substitute for advice from a qualified legal professional. Review documents for your jurisdiction and
            circumstances before using them.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4-Step Interactive Workflow Showcase
    st.subheader("⚡ How It Works")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <span class="step-number">1</span>
                <div class="step-title">Enter Details</div>
                <div class="step-desc">Select document type, define parties, covenants, and effective dates.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <span class="step-number">2</span>
                <div class="step-title">AI Drafting</div>
                <div class="step-desc">Gemini compiles formal recitals, definitions, operative clauses, and execution blocks.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <span class="step-number">3</span>
                <div class="step-title">Review & Edit</div>
                <div class="step-desc">Inspect formatted brief in real-time or switch to Edit Mode for inline clause refinement.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <span class="step-number">4</span>
                <div class="step-title">Export Document</div>
                <div class="step-desc">Download production-quality DOCX (Word), publication-grade PDF, or clean TXT.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Supported Document Types Showcase
    st.subheader("📑 Supported Document Types")
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <span class="badge-pill">🔒 Non-Disclosure Agreements (NDA)</span>
            <span class="badge-pill">💼 Employment Contracts</span>
            <span class="badge-pill">✉️ Employment Offer Letters</span>
            <span class="badge-pill">🏠 Residential & Commercial Leases</span>
            <span class="badge-pill">💻 Freelance & Contractor Agreements</span>
            <span class="badge-pill">⚙️ SaaS & Master Service Agreements</span>
            <span class="badge-pill">🤝 General Commercial Contracts</span>
            <span class="badge-pill">✨ Custom Legal Instruments</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick Start Action
    st.divider()
    col_dash_a, col_dash_b = st.columns([2, 1])
    with col_dash_a:
        st.markdown("### Ready to generate your legal document?")
        st.write("Start with a blank form or load one of our realistic legal templates.")
    with col_dash_b:
        if st.button("🚀 Launch Document Creator", type="primary", use_container_width=True):
            st.session_state["menu_nav"] = "✍️ Create Document"
            st.rerun()


# ---------------------------------------------------------
# Page 2: Create Document
# ---------------------------------------------------------
elif menu_choice == "✍️ Create Document":
    st.title("✍️ Create Legal Document")
    st.caption("Configure parties, covenants, and instructions to draft a new instrument.")

    # Legal Disclaimer
    st.markdown(
        """
        <div class="legal-alert">
            <strong>LEGAL SAFETY NOTICE:</strong> LegalEase provides AI-assisted document drafting. Review documents with a qualified attorney in your jurisdiction prior to execution.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sample Template Quick-Loader
    with st.expander("✨ Need inspiration? Load a Pre-configured Sample Template", expanded=False):
        template_selection = st.selectbox(
            "Select a pre-filled template:",
            options=["Select a template..."] + list(SAMPLE_TEMPLATES.keys()),
        )
        if st.button("Apply Selected Template"):
            if template_selection in SAMPLE_TEMPLATES:
                t_data = SAMPLE_TEMPLATES[template_selection]
                st.session_state["parties"] = t_data["parties"]
                st.session_state["terms"] = t_data["terms"]
                st.session_state["additional_instructions"] = t_data["additional_instructions"]
                # Match document type
                if "NDA" in template_selection:
                    st.session_state["document_type"] = "Non-Disclosure Agreement (NDA)"
                elif "Freelance" in template_selection:
                    st.session_state["document_type"] = "Freelance Agreement"
                elif "Employment Offer" in template_selection:
                    st.session_state["document_type"] = "Employment Offer Letter"
                elif "Lease" in template_selection:
                    st.session_state["document_type"] = "Lease Agreement"
                elif "Service" in template_selection:
                    st.session_state["document_type"] = "Service Agreement"
                st.success(f"Applied template: '{template_selection}'! Review the fields below.")
                st.rerun()

    # Form Configuration Fields
    with st.form("create_doc_form", clear_on_submit=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            doc_type_selected = st.selectbox(
                "Document Type *",
                options=DOCUMENT_TYPE_CHOICES,
                index=DOCUMENT_TYPE_CHOICES.index(st.session_state.get("document_type", "Non-Disclosure Agreement (NDA)"))
                if st.session_state.get("document_type") in DOCUMENT_TYPE_CHOICES
                else 0,
            )
            if doc_type_selected == "Custom Document Type":
                custom_type = st.text_input(
                    "Specify Custom Document Type *",
                    value="",
                    placeholder="e.g., Intellectual Property Assignment Agreement",
                )
                effective_doc_type = custom_type.strip() or "Custom Legal Agreement"
            else:
                effective_doc_type = doc_type_selected

        with c2:
            effective_date_val = st.date_input(
                "Effective Date *",
                value=st.session_state.get("effective_date", date.today()),
            )

        # Parties Field
        parties_val = st.text_area(
            "Parties Involved & Roles *",
            value=st.session_state.get("parties", ""),
            height=110,
            placeholder=(
                "Specify each party, legal entity name, designated role, and address.\n"
                "Example:\n"
                "Party A: Acme Corporation (Disclosing Party), 123 Tech Way, Suite 100, San Francisco, CA;\n"
                "Party B: Jane Doe (Receiving Party), 456 Innovation Blvd, Austin, TX"
            ),
            help="Detail full legal names, whether LLC, Inc., or Individual, and their contractual capacities.",
        )

        # Terms & Conditions Field
        terms_val = st.text_area(
            "Key Terms, Covenants & Conditions (Separate with semicolons ';' or newlines) *",
            value=st.session_state.get("terms", ""),
            height=160,
            placeholder=(
                "Payment must be made within 30 days of invoice;\n"
                "Confidentiality must be maintained for 3 years;\n"
                "Either party may terminate with 15 days notice;\n"
                "Work product shall be owned exclusively by Client upon payment."
            ),
            help="You can separate individual covenants with semicolons (;) or line breaks.",
        )

        # Additional Instructions
        additional_val = st.text_area(
            "Additional Instructions & Jurisdictional Notes (Optional)",
            value=st.session_state.get("additional_instructions", ""),
            height=85,
            placeholder="e.g., Governing law shall be the State of California. Include arbitration clause.",
        )

        # Logo Upload
        st.markdown("##### 🖼️ Company / Firm Branding (Optional)")
        uploaded_logo = st.file_uploader(
            "Upload Logo for Header (PNG, JPG, max 2MB)",
            type=["png", "jpg", "jpeg"],
            help="Embeds your firm or company logo directly into generated DOCX and PDF headers.",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "🚀 Generate Legal Document with AI",
            type="primary",
            use_container_width=True,
        )

    # Form Submission Handler
    if submitted:
        # Validation
        if not parties_val.strip():
            st.error("Please provide the parties involved before generating.")
        elif not terms_val.strip():
            st.error("Please supply at least one key term or condition.")
        else:
            # Handle Logo Processing
            logo_bytes = None
            if uploaded_logo is not None:
                # Validate size (max 2.5MB)
                if uploaded_logo.size > 2.5 * 1024 * 1024:
                    st.warning("Uploaded logo exceeds 2.5MB limit. Proceeding without logo.")
                else:
                    try:
                        logo_data = uploaded_logo.read()
                        # Validate with PIL
                        img_check = Image.open(io.BytesIO(logo_data))
                        img_check.verify()
                        logo_bytes = logo_data
                        st.session_state["uploaded_logo_bytes"] = logo_bytes
                    except Exception as e:
                        st.warning(f"Could not process uploaded image: {e}. Proceeding without logo.")

            # Save state
            st.session_state["document_type"] = effective_doc_type
            st.session_state["parties"] = parties_val.strip()
            st.session_state["terms"] = terms_val.strip()
            st.session_state["effective_date"] = effective_date_val
            st.session_state["additional_instructions"] = additional_val.strip()
            st.session_state["terms_list"] = parse_terms_list(terms_val)

            # Send generation request to Backend API (with graceful fallback)
            with st.spinner("🤖 Google Gemini is analyzing legal requirements and drafting your agreement..."):
                payload = {
                    "document_type": effective_doc_type,
                    "parties": parties_val.strip(),
                    "terms": terms_val.strip(),
                    "effective_date": effective_date_val.strftime("%Y-%m-%d"),
                    "additional_instructions": additional_val.strip(),
                }

                generation_success = False
                generated_content = ""
                meta_info = {}

                # Attempt 1: Call FastAPI Backend
                try:
                    resp = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        generated_content = data.get("content", "")
                        meta_info = {
                            "word_count": data.get("word_count", 0),
                            "char_count": data.get("char_count", 0),
                            "source": "FastAPI Backend (/generate)",
                        }
                        generation_success = True
                    else:
                        error_detail = "Server error"
                        try:
                            error_detail = resp.json().get("detail", resp.text)
                        except Exception:
                            error_detail = resp.text
                        st.warning(f"Backend API notice ({resp.status_code}): {error_detail}. Attempting direct generation...")
                except Exception as net_err:
                    st.info("FastAPI backend is not running or unreachable. Falling back to direct Gemini generator.")

                # Attempt 2: Direct Gemini generator if backend was offline or failed
                if not generation_success:
                    try:
                        direct_gen = GeminiDocumentGenerator()
                        result = direct_gen.generate_document(
                            document_type=effective_doc_type,
                            parties=parties_val.strip(),
                            terms=terms_val.strip(),
                            effective_date=effective_date_val.strftime("%Y-%m-%d"),
                            additional_instructions=additional_val.strip(),
                        )
                        generated_content = result["content"]
                        meta_info = {
                            "word_count": result.get("word_count", 0),
                            "char_count": result.get("char_count", 0),
                            "source": f"Direct Gemini SDK ({result.get('backend_used', 'Gemini')})",
                        }
                        generation_success = True
                    except GeminiGenerationError as g_err:
                        st.error(f"❌ AI Generation Error: {str(g_err)}")
                    except Exception as fatal_err:
                        st.error(f"❌ Unexpected Error: {str(fatal_err)}")

                if generation_success and generated_content:
                    st.session_state["generated_document"] = generated_content
                    st.session_state["generation_metadata"] = meta_info
                    st.success("🎉 Legal document successfully generated! Proceed to 'Document Preview' to review and download.")
                    # Automatically switch view
                    st.rerun()


# ---------------------------------------------------------
# Page 3: Document Preview & Editor
# ---------------------------------------------------------
elif menu_choice == "📄 Document Preview":
    st.title("📄 Document Preview & Export")

    current_doc = st.session_state.get("generated_document")
    if not current_doc:
        st.info("No document has been generated yet. Please go to **Create Document** to draft your first contract.")
        if st.button("👉 Go to Create Document", type="primary"):
            st.session_state["menu_nav"] = "✍️ Create Document"
            st.rerun()
    else:
        # Action Toolbar & Mode Selector
        col_view, col_meta = st.columns([2, 1])
        with col_view:
            mode_choice = st.radio(
                "Document View Mode:",
                options=["📄 Formatted Document Preview", "✏️ Edit Mode (Live Text Editor)"],
                horizontal=True,
            )

        with col_meta:
            meta = st.session_state.get("generation_metadata") or {}
            wc = len(current_doc.split())
            cc = len(current_doc)
            st.markdown(
                f"<div style='text-align:right; font-size:12px; color:#64748b; padding-top:10px;'>"
                f"<strong>{wc:,}</strong> words | <strong>{cc:,}</strong> characters<br>"
                f"Source: {meta.get('source', 'Gemini AI')}</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # VIEW MODE 1: Edit Mode
        if mode_choice == "✏️ Edit Mode (Live Text Editor)":
            st.markdown("##### ✏️ Edit Document Clauses")
            st.caption("Make any desired modifications below. All exports (TXT, DOCX, PDF) reflect your live edits.")
            edited_text = st.text_area(
                "Live Document Content Editor",
                value=current_doc,
                height=520,
                key="doc_editor_textarea",
            )
            if edited_text != current_doc:
                st.session_state["generated_document"] = edited_text
                st.toast("Draft changes saved in memory!", icon="💾")

        # VIEW MODE 2: Formatted Legal Brief HTML Preview
        else:
            st.markdown("##### 📄 Formatted Legal Brief")
            st.caption("Rendered high-fidelity preview with sanitized HTML, formal typography, and signature layout.")

            preview_html = convert_markdown_to_legal_html(
                content=current_doc,
                document_title=st.session_state.get("document_type", "LEGAL AGREEMENT"),
                effective_date=st.session_state.get("effective_date", date.today()).strftime("%B %d, %Y")
                if isinstance(st.session_state.get("effective_date"), (date, datetime))
                else str(st.session_state.get("effective_date", "")),
                parties=st.session_state.get("parties", ""),
                terms_list=st.session_state.get("terms_list", []),
            )
            # Display safely via HTML component
            st.components.v1.html(preview_html, height=680, scrolling=True)

        st.divider()

        # Download & Action Section
        st.subheader("📥 Export & Distribution")
        st.caption("Download your finalized agreement in standard industry formats with embedded styling.")

        d_col1, d_col2, d_col3, d_col4, d_col5 = st.columns([1, 1, 1, 1, 1])

        active_title = st.session_state.get("document_type", "Legal_Agreement")
        safe_base_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in active_title)
        eff_date_str = str(st.session_state.get("effective_date", date.today()))
        parties_str = st.session_state.get("parties", "")
        terms_list_val = st.session_state.get("terms_list", [])
        logo_data = st.session_state.get("uploaded_logo_bytes")

        # 1. Download TXT
        with d_col1:
            txt_output = generate_txt(
                document_text=st.session_state["generated_document"],
                document_title=active_title,
                effective_date=eff_date_str,
                parties=parties_str,
                terms_list=terms_list_val,
            )
            st.download_button(
                label="📄 Download TXT",
                data=txt_output.encode("utf-8"),
                file_name=f"{safe_base_name}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # 2. Download DOCX
        with d_col2:
            try:
                docx_buffer = generate_docx(
                    document_text=st.session_state["generated_document"],
                    document_title=active_title,
                    effective_date=eff_date_str,
                    parties=parties_str,
                    terms_list=terms_list_val,
                    logo_bytes=logo_data,
                )
                st.download_button(
                    label="📘 Download DOCX",
                    data=docx_buffer.getvalue(),
                    file_name=f"{safe_base_name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as docx_err:
                st.error(f"DOCX compilation failed: {docx_err}")

        # 3. Download PDF
        with d_col3:
            try:
                pdf_buffer = generate_pdf(
                    document_text=st.session_state["generated_document"],
                    document_title=active_title,
                    effective_date=eff_date_str,
                    parties=parties_str,
                    terms_list=terms_list_val,
                    logo_bytes=logo_data,
                )
                st.download_button(
                    label="📕 Download PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"{safe_base_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as pdf_err:
                st.error(f"PDF compilation failed: {pdf_err}")

        # 4. Regenerate Button
        with d_col4:
            if st.button("🔄 Regenerate", use_container_width=True):
                with st.spinner("Regenerating document with current parameters..."):
                    try:
                        direct_gen = GeminiDocumentGenerator()
                        result = direct_gen.generate_document(
                            document_type=st.session_state["document_type"],
                            parties=st.session_state["parties"],
                            terms=st.session_state["terms"],
                            effective_date=str(st.session_state["effective_date"]),
                            additional_instructions=st.session_state.get("additional_instructions", ""),
                        )
                        st.session_state["generated_document"] = result["content"]
                        st.success("Regenerated successfully!")
                        st.rerun()
                    except Exception as regen_err:
                        st.error(f"Regeneration failed: {regen_err}")

        # 5. Clear / Reset
        with d_col5:
            if st.button("🗑️ Reset / New", use_container_width=True):
                st.session_state["generated_document"] = None
                st.session_state["generation_metadata"] = None
                st.rerun()


# ---------------------------------------------------------
# Page 4: About & Legal
# ---------------------------------------------------------
elif menu_choice == "ℹ️ About & Legal":
    st.title("ℹ️ About LegalEase")
    st.markdown("### Next-Generation AI Legal Drafting & Document Compilation")

    st.markdown(
        """
        **LegalEase** is an enterprise-grade legal engineering tool built to streamline the initial drafting,
        structuring, and formatting of commercial agreements, employment instruments, non-disclosure contracts,
        and bespoke legal documents.
        """
    )

    st.divider()

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### 🏛️ Architectural Stack")
        st.markdown(
            """
            - **Backend Framework**: FastAPI (High-performance ASGI API with Pydantic validation)
            - **Frontend UI**: Streamlit with custom responsive SaaS CSS styling
            - **AI Engine**: Google Gemini (official `google-genai` SDK with temperature tuning)
            - **Document Generation**:
              - `python-docx` for structured Microsoft Word (.docx) documents
              - `fpdf2` for publication-grade PDF documents with dynamic pagination
              - UTF-8 clean ASCII Plain Text generator
              - Safe XSS-sanitized HTML previewer
            """
        )

    with col_a2:
        st.markdown("#### 🔒 Security & Privacy")
        st.markdown(
            """
            - **Zero Key Leakage**: API credentials are read exclusively from environment variables (`.env`).
            - **No Content Logging**: Sensitive party identities and contractual terms are never written to public logs.
            - **XSS Protection**: All user-provided strings and generated content undergo rigorous tag sanitization.
            - **File Integrity**: Image uploads are verified via PIL dimensions and size-restricted (<2.5 MB).
            """
        )

    st.divider()

    # Prominent Disclaimer Section
    st.subheader("⚖️ Legal Disclaimer & Terms of Use")
    st.markdown(
        """
        <div class="legal-alert" style="font-size: 13px;">
            <strong>LEGAL REPRESENTATION DISCLAIMER:</strong><br>
            LegalEase provides AI-generated legal information and drafting assistance. It is not a law firm,
            does not provide legal representation, and does not establish an attorney-client relationship.
            Laws and regulations vary substantially across local, state, federal, and international jurisdictions.
            Always consult a qualified attorney licensed in your jurisdiction to review, tailor, and validate
            any agreement or document prior to execution.
        </div>
        """,
        unsafe_allow_html=True,
    )
