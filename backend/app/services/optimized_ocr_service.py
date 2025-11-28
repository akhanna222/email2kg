"""
Optimized OCR processing service with improved accuracy and performance.

Uses multiple OCR engines and preprocessing techniques for better results.
"""
from typing import Dict, Any, Optional, List
import os
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import logging

logger = logging.getLogger(__name__)


class OptimizedOCRService:
    """Enhanced OCR service with preprocessing and multiple engine support."""

    def __init__(self):
        self.dpi = 300  # Higher DPI for better OCR
        self.tesseract_config = '--oem 3 --psm 6'  # Optimize Tesseract settings

    def extract_text_from_pdf(
        self,
        pdf_path: str,
        use_preprocessing: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from PDF with optimized OCR.

        Args:
            pdf_path: Path to PDF file
            use_preprocessing: Apply image preprocessing

        Returns:
            Dictionary with text and confidence scores
        """
        try:
            # Try direct text extraction first (for text-based PDFs)
            text = self._try_direct_extraction(pdf_path)

            if text and len(text.strip()) > 100:
                return {
                    'text': text,
                    'method': 'direct',
                    'confidence': 1.0,
                    'pages': 1
                }

            # Fall back to OCR for scanned PDFs
            return self._extract_with_ocr(pdf_path, use_preprocessing)

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                'text': '',
                'method': 'failed',
                'confidence': 0.0,
                'error': str(e)
            }

    def _try_direct_extraction(self, pdf_path: str) -> str:
        """Try extracting text directly from PDF (for text-based PDFs)."""
        try:
            import PyPDF2

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''

                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'

                return text.strip()

        except Exception as e:
            logger.debug(f"Direct extraction failed: {e}")
            return ''

    def _extract_with_ocr(
        self,
        pdf_path: str,
        use_preprocessing: bool = True
    ) -> Dict[str, Any]:
        """Extract text using OCR with preprocessing."""
        try:
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt='png',
                thread_count=4  # Parallel processing
            )

            all_text = []
            confidences = []

            for page_num, image in enumerate(images, 1):
                if use_preprocessing:
                    # Preprocess image for better OCR
                    image = self._preprocess_image(image)

                # Extract text with Tesseract
                ocr_data = pytesseract.image_to_data(
                    image,
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )

                # Filter low-confidence results
                page_text = self._extract_high_confidence_text(ocr_data)
                all_text.append(page_text)

                # Calculate average confidence
                valid_conf = [
                    int(conf) for conf in ocr_data['conf']
                    if conf != '-1' and int(conf) > 0
                ]
                if valid_conf:
                    confidences.append(np.mean(valid_conf))

            final_text = '\n\n'.join(all_text)
            avg_confidence = np.mean(confidences) if confidences else 0.0

            return {
                'text': final_text,
                'method': 'ocr',
                'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'pages': len(images)
            }

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {
                'text': '',
                'method': 'ocr_failed',
                'confidence': 0.0,
                'error': str(e)
            }

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Apply preprocessing to improve OCR accuracy.

        Techniques:
        - Grayscale conversion
        - Noise reduction
        - Contrast enhancement
        - Binarization (Otsu's method)
        - Deskewing
        """
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Binarization using Otsu's method
        _, binary = cv2.threshold(
            enhanced,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Deskew image
        deskewed = self._deskew_image(binary)

        # Convert back to PIL Image
        return Image.fromarray(deskewed)

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image to correct rotation."""
        coords = np.column_stack(np.where(image > 0))

        if len(coords) == 0:
            return image

        angle = cv2.minAreaRect(coords)[-1]

        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

    def _extract_high_confidence_text(
        self,
        ocr_data: Dict[str, List],
        min_confidence: int = 30
    ) -> str:
        """
        Extract only high-confidence text from OCR results.

        Args:
            ocr_data: Tesseract OCR output
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            Extracted text
        """
        lines = {}  # Group by line number

        for i, conf in enumerate(ocr_data['conf']):
            if conf == '-1':
                continue

            conf_score = int(conf)
            if conf_score >= min_confidence:
                line_num = ocr_data['line_num'][i]
                text = ocr_data['text'][i]

                if text.strip():
                    if line_num not in lines:
                        lines[line_num] = []
                    lines[line_num].append(text)

        # Reconstruct text maintaining line structure
        result = []
        for line_num in sorted(lines.keys()):
            line_text = ' '.join(lines[line_num])
            result.append(line_text)

        return '\n'.join(result)

    def extract_document_regions(
        self,
        image: Image.Image
    ) -> List[Dict[str, Any]]:
        """
        Detect and extract different regions of a document.

        Useful for structured documents like invoices, forms, etc.

        Returns:
            List of regions with their bounding boxes and text
        """
        img_array = np.array(image)

        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Detect text regions using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

        # Binarize
        _, binary = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Connect nearby regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            connected,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        regions = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # Filter small regions
            if w < 50 or h < 20:
                continue

            # Extract region
            region_img = image.crop((x, y, x + w, y + h))

            # OCR on region
            region_text = pytesseract.image_to_string(
                region_img,
                config=self.tesseract_config
            )

            if region_text.strip():
                regions.append({
                    'bbox': {'x': x, 'y': y, 'width': w, 'height': h},
                    'text': region_text.strip(),
                    'area': w * h
                })

        # Sort by position (top to bottom, left to right)
        regions.sort(key=lambda r: (r['bbox']['y'], r['bbox']['x']))

        return regions

    def detect_document_layout(
        self,
        image: Image.Image
    ) -> Dict[str, Any]:
        """
        Detect document layout structure.

        Returns:
            Dictionary with layout information (header, footer, columns, etc.)
        """
        width, height = image.size

        layout = {
            'width': width,
            'height': height,
            'header_region': {'y': 0, 'height': int(height * 0.15)},
            'footer_region': {'y': int(height * 0.85), 'height': int(height * 0.15)},
            'body_region': {'y': int(height * 0.15), 'height': int(height * 0.70)},
            'estimated_columns': 1
        }

        # Detect columns by analyzing white space
        img_array = np.array(image.convert('L'))
        vertical_projection = np.sum(img_array < 200, axis=0)

        # Find valleys in projection (potential column boundaries)
        threshold = np.max(vertical_projection) * 0.1
        in_valley = vertical_projection < threshold
        valleys = []

        for i in range(1, len(in_valley)):
            if in_valley[i] and not in_valley[i-1]:
                valleys.append(i)

        # Estimate columns based on significant valleys
        if len(valleys) >= 1:
            layout['estimated_columns'] = len(valleys) + 1
            layout['column_boundaries'] = valleys

        return layout
