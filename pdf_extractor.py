"""
pdf_extractor.py
----------------
Handles PDF file reading and text extraction using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF
import streamlit as st


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract all text content from an uploaded PDF file.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        A single string containing all extracted text from the PDF.

    Raises:
        ValueError: If the PDF is empty or has no extractable text.
    """
    try:
        # Read the uploaded file bytes
        pdf_bytes = uploaded_file.read()

        # Open the PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        if len(doc) == 0:
            raise ValueError("The uploaded PDF has no pages.")

        full_text = []

        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")  # Extract plain text
            if page_text.strip():
                full_text.append(f"--- Page {page_num + 1} ---\n{page_text}")

        doc.close()

        if not full_text:
            raise ValueError(
                "No extractable text found. The PDF may be scanned or image-based."
            )

        combined_text = "\n\n".join(full_text)
        return combined_text

    except fitz.FileDataError:
        raise ValueError("Invalid or corrupted PDF file. Please upload a valid PDF.")
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def get_pdf_metadata(uploaded_file) -> dict:
    """
    Extract basic metadata from a PDF file.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Dictionary containing page count and file size.
    """
    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        metadata = {
            "page_count": len(doc),
            "file_size_kb": round(len(pdf_bytes) / 1024, 2),
            "title": doc.metadata.get("title", "Unknown"),
            "author": doc.metadata.get("author", "Unknown"),
        }
        doc.close()
        # Reset file pointer for subsequent reads
        uploaded_file.seek(0)
        return metadata
    except Exception:
        uploaded_file.seek(0)
        return {"page_count": 0, "file_size_kb": 0, "title": "Unknown", "author": "Unknown"}
