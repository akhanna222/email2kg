import PyPDF2
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from typing import Optional
import os


class PDFService:
    """Service for extracting text from PDF documents."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from PDF. First tries PyPDF2, falls back to OCR if needed.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        # Try PyPDF2 first (faster for text-based PDFs)
        text = PDFService._extract_with_pypdf(file_path)

        # If text is too short, the PDF might be scanned - try OCR
        if len(text.strip()) < 50:
            text = PDFService._extract_with_ocr(file_path)

        return text

    @staticmethod
    def _extract_with_pypdf(file_path: str) -> str:
        """Extract text using PyPDF2."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return ""

    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> str:
        """Extract text using pdfplumber (alternative to PyPDF2)."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            return ""

    @staticmethod
    def _extract_with_ocr(file_path: str) -> str:
        """Extract text using OCR (Tesseract)."""
        try:
            # Convert PDF to images
            images = convert_from_path(file_path)

            text = ""
            for i, image in enumerate(images):
                # Perform OCR on each page
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"

            return text.strip()
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""

    @staticmethod
    def get_metadata(file_path: str) -> dict:
        """Extract PDF metadata."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata

                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "creation_date": metadata.get("/CreationDate", ""),
                    "num_pages": len(pdf_reader.pages)
                }
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {}
