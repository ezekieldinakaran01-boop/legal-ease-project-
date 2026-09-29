"""Gemini AI Core integration for legal document generation."""

import os
import re
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger("legalease.ai_core")


class GeminiGenerationError(Exception):
    """Custom exception raised when document generation fails."""
    pass


class GeminiDocumentGenerator:
    """Enterprise-grade wrapper for Google Gemini API specialized in legal document drafting."""

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize the Gemini generator with API credentials and model configuration.

        Priority order:
        1. Explicitly passed argument
        2. Environment variable GEMINI_API_KEY / GEMINI_MODEL
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

    def is_configured(self) -> bool:
        """Check if a non-placeholder API key is available."""
        if not self.api_key:
            return False
        cleaned = self.api_key.strip()
        if not cleaned or cleaned == "your_gemini_api_key_here" or "your_" in cleaned.lower():
            return False
        return True

    def build_prompt(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Construct a rigorous, structured prompt directing Gemini to produce a professional legal document."""
        return f"""You are a specialized legal drafting engine. Generate a formal, production-quality, enforceable-style legal document for the following request.

DOCUMENT TYPE: {document_type}
EFFECTIVE DATE: {effective_date}

PARTIES INVOLVED:
{parties}

KEY TERMS, CONDITIONS & COVENANTS:
{terms}

ADDITIONAL DRAFTING INSTRUCTIONS & JURISDICTION NOTES:
{additional_instructions if additional_instructions else "Standard professional commercial legal standards."}

DRAFTING REQUIREMENTS:
1. Title: Create a prominent, formal, centered-style legal title matching the document type (e.g., NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT).
2. Preamble & Recitals: Detail the introductory statement identifying the Effective Date and recitals ("WHEREAS...") setting forth the commercial background and mutual intentions of the parties.
3. Parties: Explicitly detail each party with designated roles (e.g., "Disclosing Party", "Receiving Party", "Employer", "Contractor", "Lessor", "Lessee"), including addresses/jurisdictions as supplied.
4. Definitions: Include formal definitions of key capitalized legal terms used throughout the document (e.g., Confidential Information, Services, Deliverables, Work Product).
5. Core Terms & Provisions: Expand the user's provided terms into clear, robust, enforceable numbered articles or sections (e.g., SECTION 1, SECTION 2...).
6. Rights & Obligations: Distinctly spell out the affirmative duties, negative covenants, and standard of care for each party.
7. Compensation / Payment / Consideration: Explicitly outline payment schedules, invoicing terms, late fees, or legal consideration if relevant to the document type.
8. Term & Termination: Specify the duration of the agreement, notice periods for termination (for cause and for convenience), and survival clauses.
9. Confidentiality / IP Rights: Detail proprietary rights, non-use, and protection standards where appropriate for the document type.
10. Representations & Warranties: Standard mutual legal warranties of authority and non-infringement.
11. Indemnification & Limitation of Liability: Standard commercial limitation of consequential damages and indemnification provisions.
12. Governing Law & Dispute Resolution: Include a governing law clause with clear bracketed placeholders (e.g., "[State/Province/Jurisdiction]") if not specified.
13. Miscellaneous: Standard boilerplate clauses including Severability, Entire Agreement, Amendments in Writing, Notices, and Counterparts.
14. Signature Block: Provide a formal closing declaration ("IN WITNESS WHEREOF...") followed by side-by-side or stacked signature execution blocks for every party, including:
    - Party Legal Name
    - By: __________________________
    - Name: ________________________
    - Title: _______________________
    - Date: ________________________
15. Disclaimer Notice: At the very end, after signatures, include this exact notice:
    "---
    NOTICE & DISCLAIMER: This document was prepared with the assistance of LegalEase AI. It is intended solely as an initial draft and information resource. Laws vary significantly across jurisdictions. This document does not constitute legal advice, and should be reviewed and customized by a licensed attorney prior to execution."

SAFETY AND QUALITY RULES:
- Generate ONLY the legal document text.
- Do NOT output conversational filler like "Here is your agreement", "Certainly!", or "I hope this helps".
- Do NOT wrap the entire response in markdown code blocks (do NOT use ```markdown or ```).
- Never fabricate financial numbers, specific names, or critical facts not supplied by the user. Use clear bracketed placeholders (e.g., [Insert Interest Rate %], [Insert City, State]) when information is missing.
- Ensure formatting is clear, with capitalized section titles and numbered paragraphs suitable for plain text, DOCX, and PDF conversion.
"""

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
        additional_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate the complete legal document using the configured Google Gemini API.

        Returns a dictionary containing the generated content and generation metadata.
        Raises GeminiGenerationError on configuration or API errors.
        """
        if not self.is_configured():
            raise GeminiGenerationError(
                "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable "
                "in your .env file or hosting environment. You can obtain a key at https://aistudio.google.com/."
            )

        prompt = self.build_prompt(
            document_type=document_type,
            parties=parties,
            terms=terms,
            effective_date=effective_date,
            additional_instructions=additional_instructions
        )

        generated_text = ""
        backend_used = ""

        # Try Google GenAI SDK (google.genai - modern official unified SDK)
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            logger.info("Calling Gemini API via google.genai SDK with model %s", self.model_name)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Low temperature for formal legal drafting
                    max_output_tokens=8192,
                )
            )
            if response and hasattr(response, "text") and response.text:
                generated_text = response.text
                backend_used = f"google-genai ({self.model_name})"
        except ImportError:
            logger.info("google-genai not found, attempting fallback to google.generativeai")
        except Exception as e:
            logger.warning("google.genai call failed: %s. Attempting fallback if available.", str(e))
            # If it failed due to authentication or invalid key, raise immediately
            err_msg = str(e).lower()
            if "api key not valid" in err_msg or "invalid_argument" in err_msg or "permission_denied" in err_msg:
                raise GeminiGenerationError(f"Gemini API Authentication Failed: {e}")

        # Fallback to google.generativeai SDK if text is still empty
        if not generated_text:
            try:
                import google.generativeai as legacy_genai

                legacy_genai.configure(api_key=self.api_key)
                model = legacy_genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={"temperature": 0.2}
                )
                logger.info("Calling Gemini API via google.generativeai SDK with model %s", self.model_name)
                response = model.generate_content(prompt)
                if response and hasattr(response, "text") and response.text:
                    generated_text = response.text
                    backend_used = f"google-generativeai ({self.model_name})"
            except Exception as legacy_err:
                logger.error("Both Gemini SDK attempts failed: %s", legacy_err)
                raise GeminiGenerationError(
                    f"Gemini document generation failed: {legacy_err}. "
                    "Please verify your GEMINI_API_KEY, model availability, and network connection."
                )

        if not generated_text or not generated_text.strip():
            raise GeminiGenerationError("Gemini returned an empty response. Please review input parameters and try again.")

        # Post-processing: remove accidental markdown code fences
        cleaned_text = generated_text.strip()
        cleaned_text = re.sub(r"^```(?:markdown|text)?\n", "", cleaned_text)
        cleaned_text = re.sub(r"\n```$", "", cleaned_text)
        cleaned_text = cleaned_text.strip()

        words = len(cleaned_text.split())
        chars = len(cleaned_text)

        return {
            "content": cleaned_text,
            "document_type": document_type,
            "model_used": self.model_name,
            "backend_used": backend_used,
            "word_count": words,
            "char_count": chars,
        }
