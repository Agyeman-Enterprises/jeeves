"""
Utility functions for text extraction and classification.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

LOGGER = logging.getLogger(__name__)

# Business entity keywords for classification
ENTITY_KEYWORDS = {
    "ohimaa": ["ohimaa", "ohimaa medical"],
    "purrkoin": ["purrkoin", "purrkoin game"],
    "meowtopia": ["meowtopia"],
    "election empire": ["election empire"],
    "bookadoc2u": ["bookadoc2u", "bookadoc"],
    "inkwell": ["inkwell", "inkwell publishing"],
    "sva": ["sva", "scientia vitae academy"],
    "learning studio": ["learning studio", "the learning studio"],
    "whiskers": ["whiskers", "whiskers and wanderlust", "whiskersnwanderlust"],
    "dramd": ["dramd", "dramd"],
    "flyryt": ["flyryt"],
    "ghexit": ["ghexit"],
    "scribemd": ["scribemd"],
    "solopractice": ["solopractice"],
    "accesscare": ["accesscare"],
    "medrx": ["medrx"],
    "taxrx": ["taxrx"],
    "a3design": ["a3design", "a3 design"],
    "kraftforge": ["kraftforge"],
    "medmaker": ["medmaker"],
    "imho": ["imho media"],
    "furfubu": ["furfubu"],
    "inov8if": ["inov8if"],
}


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    """
    Extract text from file bytes based on file extension.
    Supports PDF, DOCX, TXT, MD, and other text formats.
    """
    path = Path(filename)
    suffix = path.suffix.lower()

    # Text files
    if suffix in {".txt", ".md", ".markdown", ".json", ".yaml", ".yml", ".csv"}:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return data.decode("latin-1")
            except Exception as exc:
                LOGGER.warning("Failed to decode text file %s: %s", filename, exc)
                return ""

    # PDF files
    if suffix == ".pdf":
        try:
            import pypdf
            from io import BytesIO

            pdf_reader = pypdf.PdfReader(BytesIO(data))
            text_parts = []
            for page in pdf_reader.pages:
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                except Exception as exc:
                    LOGGER.debug("Failed to extract text from PDF page: %s", exc)
            return "\n\n".join(text_parts)
        except ImportError:
            LOGGER.warning("pypdf not installed. Cannot extract text from PDF: %s", filename)
            return ""
        except Exception as exc:
            LOGGER.warning("Failed to extract text from PDF %s: %s", filename, exc)
            return ""

    # DOCX files
    if suffix == ".docx":
        try:
            from docx import Document
            from io import BytesIO

            doc = Document(BytesIO(data))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            LOGGER.warning("python-docx not installed. Cannot extract text from DOCX: %s", filename)
            return ""
        except Exception as exc:
            LOGGER.warning("Failed to extract text from DOCX %s: %s", filename, exc)
            return ""

    # Excel files
    if suffix in {".xls", ".xlsx"}:
        try:
            import pandas as pd
            from io import BytesIO

            excel_file = pd.ExcelFile(BytesIO(data))
            text_parts = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                text_parts.append(f"Sheet: {sheet_name}\n{df.to_string()}")
            return "\n\n".join(text_parts)
        except ImportError:
            LOGGER.warning("pandas/openpyxl not installed. Cannot extract text from Excel: %s", filename)
            return ""
        except Exception as exc:
            LOGGER.warning("Failed to extract text from Excel %s: %s", filename, exc)
            return ""

    # Default: try to decode as text
    try:
        return data.decode("utf-8")
    except Exception:
        LOGGER.warning("Could not extract text from %s (unsupported format)", filename)
        return ""


def classify_entity(path: str) -> Optional[str]:
    """
    Classify document entity based on path and content.
    Returns entity name if found, None otherwise.
    """
    path_lower = path.lower()

    for entity, keywords in ENTITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in path_lower:
                return entity

    return None


def classify_tags(text: str, path: str = "") -> List[str]:
    """
    Classify document tags based on content and path.
    Returns list of relevant tags.
    """
    tags = []
    text_lower = text.lower()
    path_lower = path.lower()

    # Document type tags
    if any(ext in path_lower for ext in [".pdf", ".docx", ".doc"]):
        tags.append("document")
    if ".pdf" in path_lower:
        tags.append("pdf")
    if ".docx" in path_lower or ".doc" in path_lower:
        tags.append("word")
    if ".xls" in path_lower or ".xlsx" in path_lower:
        tags.append("spreadsheet")

    # Content-based tags
    if any(word in text_lower for word in ["contract", "agreement", "lease"]):
        tags.append("contract")
    if any(word in text_lower for word in ["invoice", "receipt", "bill"]):
        tags.append("financial")
    if any(word in text_lower for word in ["investor", "deck", "pitch", "presentation"]):
        tags.append("investor")
    if any(word in text_lower for word in ["engineering", "technical", "specification"]):
        tags.append("engineering")
    if any(word in text_lower for word in ["legal", "law", "attorney"]):
        tags.append("legal")
    if any(word in text_lower for word in ["medical", "patient", "clinical"]):
        tags.append("medical")

    # Folder-based tags
    if "receipts" in path_lower or "bills" in path_lower:
        tags.append("receipt")
    if "contracts" in path_lower:
        tags.append("contract")
    if "investor" in path_lower or "fundraising" in path_lower:
        tags.append("investor")

    return list(set(tags))  # Remove duplicates

