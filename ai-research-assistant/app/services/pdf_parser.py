"""
PDF Parser Service - Extracts text and metadata from documents
Phase 2: Advanced extraction with structure preservation
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import PyPDF2
import base64
from io import BytesIO
import re
import logging
from dataclasses import dataclass

try:
    import fitz
except Exception:  # pragma: no cover - optional dependency
    fitz = None

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:  # pragma: no cover - optional dependency
    RapidOCR = None

from app.config import OPENAI_API_KEY, OPENAI_OCR_MODEL

logger = logging.getLogger(__name__)


@dataclass
class Page:
    """Represents a single page of extracted content"""
    page_number: int
    text: str
    length: int
    metadata: Dict = None
    raw_text: str = None
    tables: List[str] = None


class PDFParser:
    """Extract text and metadata from PDF files with advanced features"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt']
        self.extraction_methods = ['standard', 'preserve_layout', 'ocr']
        self._rapid_ocr = RapidOCR() if RapidOCR is not None else None
    
    def extract_text(self, file_path: str) -> Dict:
        """
        Extract text from document file
        
        Args:
            file_path: Path to the document file
        
        Returns:
            Dictionary with extracted text and metadata
            {
                "full_text": "...",
                "pages": [
                    {"page_num": 1, "text": "...", "length": 150},
                    ...
                ],
                "metadata": {
                    "total_pages": 10,
                    "title": "...",
                    "author": "..."
                },
                "total_characters": 5000
            }
        """
        file_path = Path(file_path)
        
        try:
            if file_path.suffix.lower() == '.txt':
                return self._extract_txt(file_path)
            elif file_path.suffix.lower() == '.pdf':
                return self._extract_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise

    def _render_pdf_page_image(self, file_path: Path, page_index: int) -> str:
        """Render a PDF page to PNG bytes for OCR."""
        if fitz is None:
            raise RuntimeError("PyMuPDF is not installed")

        doc = fitz.open(file_path)
        try:
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            return pix.tobytes("png")
        finally:
            doc.close()

    def _extract_rapidocr_text(self, ocr_result) -> str:
        if not ocr_result:
            return ""

        lines = []
        for item in ocr_result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                text = str(item[1]).strip()
                if text:
                    lines.append(text)
        return "\n".join(lines).strip()

    def _ocr_pdf_locally(self, file_path: Path, total_pages: int) -> Dict:
        if self._rapid_ocr is None:
            raise RuntimeError("RapidOCR is not installed")
        if fitz is None:
            raise RuntimeError("PyMuPDF is not installed")

        pages_data = []
        full_text_parts = []

        for page_index in range(total_pages):
            page_number = page_index + 1
            image_bytes = self._render_pdf_page_image(file_path, page_index)
            ocr_result, _elapsed = self._rapid_ocr(image_bytes)
            page_text = self._extract_rapidocr_text(ocr_result)
            cleaned_text = self._clean_text(page_text)

            pages_data.append(
                {
                    "page_num": page_number,
                    "text": cleaned_text,
                    "raw_text": page_text,
                    "length": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                    "structure": self._detect_structure(cleaned_text),
                    "sections": self._extract_sections(cleaned_text),
                    "ocr_fallback": True,
                    "ocr_engine": "rapidocr_onnxruntime",
                }
            )

            if cleaned_text:
                full_text_parts.append(f"\n--- Page {page_number} ---\n{cleaned_text}")

        full_text = "".join(full_text_parts).strip()
        return {
            "full_text": full_text,
            "pages": pages_data,
            "metadata": {
                "total_pages": total_pages,
                "title": file_path.stem,
                "author": "Unknown",
                "creation_date": "Unknown",
                "producer": "RapidOCR fallback",
            },
            "total_characters": len(full_text),
            "total_words": len(full_text.split()),
            "extraction_quality": {
                "score": 100 if full_text else 0,
                "level": "excellent" if full_text else "poor",
                "issues": [] if full_text else ["Local OCR fallback did not extract any text"],
                "metrics": {
                    "avg_word_length": 0,
                    "avg_sentence_length": 0,
                    "special_char_ratio": 0,
                },
            },
            "extracted_pages": sum(1 for page in pages_data if page.get("text", "").strip()),
            "ocr_fallback": True,
            "ocr_engine": "rapidocr_onnxruntime",
        }

    def _ocr_pdf_with_openai(self, file_path: Path, total_pages: int) -> Dict:
        """Use OpenAI vision OCR for PDFs that have no extractable text."""
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if OpenAI is None:
            raise RuntimeError("openai package is not installed")
        if fitz is None:
            raise RuntimeError("PyMuPDF is not installed")

        client = OpenAI(api_key=OPENAI_API_KEY)
        pages_data = []
        full_text_parts = []

        for page_index in range(total_pages):
            page_number = page_index + 1
            image_data_url = self._render_pdf_page_image(file_path, page_index)
            response = client.responses.create(
                model=OPENAI_OCR_MODEL,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "Extract all visible text from this PDF page. "
                                    "Preserve headings and paragraph breaks. "
                                    "Return only the text content, no commentary."
                                ),
                            },
                            {
                                "type": "input_image",
                                "image_url": image_data_url,
                            },
                        ],
                    }
                ],
            )

            page_text = (getattr(response, "output_text", "") or "").strip()
            cleaned_text = self._clean_text(page_text)
            pages_data.append(
                {
                    "page_num": page_number,
                    "text": cleaned_text,
                    "raw_text": page_text,
                    "length": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                    "structure": self._detect_structure(cleaned_text),
                    "sections": self._extract_sections(cleaned_text),
                    "ocr_fallback": True,
                }
            )
            if cleaned_text:
                full_text_parts.append(f"\n--- Page {page_number} ---\n{cleaned_text}")

        full_text = "".join(full_text_parts).strip()
        return {
            "full_text": full_text,
            "pages": pages_data,
            "metadata": {
                "total_pages": total_pages,
                "title": file_path.stem,
                "author": "Unknown",
                "creation_date": "Unknown",
                "producer": "OpenAI OCR fallback",
            },
            "total_characters": len(full_text),
            "total_words": len(full_text.split()),
            "extraction_quality": {
                "score": 100 if full_text else 0,
                "level": "excellent" if full_text else "poor",
                "issues": [] if full_text else ["OCR fallback did not extract any text"],
                "metrics": {
                    "avg_word_length": 0,
                    "avg_sentence_length": 0,
                    "special_char_ratio": 0,
                },
            },
            "extracted_pages": sum(1 for page in pages_data if page.get("text", "").strip()),
            "ocr_fallback": True,
        }
    
    def _extract_pdf(self, file_path: Path) -> Dict:
        """Extract text from PDF file with advanced features"""
        try:
            pages_data = []
            extracted_pages = 0
            full_text_parts = []
            
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                
                # Extract metadata
                metadata = pdf_reader.metadata or {}
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    
                    # Clean up text
                    cleaned_text = self._clean_text(text)
                    
                    # Detect structure
                    structure = self._detect_structure(text)
                    
                    pages_data.append({
                        "page_num": page_num,
                        "text": cleaned_text,
                        "raw_text": text,
                        "length": len(cleaned_text),
                        "word_count": len(cleaned_text.split()),
                        "structure": structure,
                        "sections": self._extract_sections(cleaned_text)
                    })

                    if cleaned_text.strip():
                        extracted_pages += 1
                        full_text_parts.append(f"\n--- Page {page_num} ---\n{cleaned_text}")
            
            logger.info(f"Successfully extracted {total_pages} pages from {file_path.name}")

            full_text = "".join(full_text_parts).strip()
            extraction_quality = self._assess_extraction_quality(full_text)
            if extracted_pages == 0:
                logger.warning(f"No text extracted from {file_path.name}; attempting local OCR fallback")
                try:
                    return self._ocr_pdf_locally(file_path, total_pages)
                except Exception as local_ocr_error:
                    logger.warning(f"Local OCR failed for {file_path.name}: {local_ocr_error}; attempting OpenAI OCR fallback")
                    try:
                        return self._ocr_pdf_with_openai(file_path, total_pages)
                    except Exception as ocr_error:
                        logger.error(f"OCR fallback failed for {file_path.name}: {ocr_error}")
                        extraction_quality = {
                            "score": 0,
                            "level": "poor",
                            "issues": [
                                "No extractable text found in PDF - the document may be image-based or scanned",
                                f"Local OCR failed: {local_ocr_error}",
                                f"OpenAI OCR failed: {ocr_error}",
                            ],
                            "metrics": {
                                "avg_word_length": 0,
                                "avg_sentence_length": 0,
                                "special_char_ratio": 0,
                            },
                        }
                        return {
                            "full_text": "",
                            "pages": pages_data,
                            "metadata": {
                                "total_pages": total_pages,
                                "title": pdf_reader.metadata.get("/Title", "Unknown") if pdf_reader.metadata else "Unknown",
                                "author": pdf_reader.metadata.get("/Author", "Unknown") if pdf_reader.metadata else "Unknown",
                                "creation_date": str(pdf_reader.metadata.get("/CreationDate", "Unknown")) if pdf_reader.metadata else "Unknown",
                                "producer": pdf_reader.metadata.get("/Producer", "Unknown") if pdf_reader.metadata else "Unknown",
                            },
                            "total_characters": 0,
                            "total_words": 0,
                            "extraction_quality": extraction_quality,
                            "extracted_pages": 0,
                            "ocr_error": str(ocr_error),
                            "ocr_attempted": True,
                        }
            
            return {
                "full_text": full_text,
                "pages": pages_data,
                "metadata": {
                    "total_pages": total_pages,
                    "title": metadata.get("/Title", "Unknown"),
                    "author": metadata.get("/Author", "Unknown"),
                    "creation_date": str(metadata.get("/CreationDate", "Unknown")),
                    "producer": metadata.get("/Producer", "Unknown")
                },
                "total_characters": len(full_text),
                "total_words": len(full_text.split()),
                "extraction_quality": extraction_quality,
                "extracted_pages": extracted_pages,
                "ocr_attempted": False,
                "ocr_engine": None,
            }
        
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path.name}: {str(e)}")
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Reduce multiple blank lines to at most two (preserve paragraph boundaries)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Collapse multiple spaces/tabs but preserve newlines
        text = re.sub(r'[ \t]+', ' ', text)

        # Remove control characters except newline and tab
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

        # Fix common OCR errors (apply replacements)
        text = self._fix_ocr_errors(text)

        return text.strip()
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR/extraction errors"""
        replacements = {
            'lI': 'li',  # Common confusion
            '0O': 'oo',  # Zero and O
            '|': 'I',    # Pipe to I (context dependent)
        }
        # Apply simple replacements conservatively
        for old, new in replacements.items():
            if old in text:
                text = text.replace(old, new)

        return text
    
    def _detect_structure(self, text: str) -> Dict:
        """Detect document structure"""
        structure = {
            "has_headers": bool(re.search(r'^[A-Z][A-Z\s]+$', text, re.MULTILINE)),
            "has_lists": bool(re.search(r'^\s*[-•*]\s', text, re.MULTILINE)),
            "has_numbers": bool(re.search(r'\d+', text)),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "line_count": len(text.split('\n'))
        }
        return structure
    
    def _extract_sections(self, text: str) -> List[Dict]:
        """Extract main sections/paragraphs"""
        sections = []
        
        # Split by multiple line breaks (paragraphs)
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:  # Only meaningful paragraphs
                sections.append({
                    "text": para,
                    "length": len(para),
                    "word_count": len(para.split())
                })
        
        return sections
    
    def _assess_extraction_quality(self, text: str) -> Dict:
        """Assess quality of extracted text"""
        if not text:
            return {"score": 0, "level": "poor", "issues": ["Empty text"]}
        
        words = text.split()
        sentences = text.split('.')
        
        # Calculate metrics
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Detect potential issues
        issues = []
        score = 100
        
        if avg_word_length < 3:
            issues.append("Unusually short words - possible OCR error")
            score -= 20
        
        if avg_word_length > 15:
            issues.append("Unusually long words - possible extraction error")
            score -= 15
        
        if len(text) < 100:
            issues.append("Very short text - might be mostly image/tables")
            score -= 30
        
        # Special character ratio
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' \n\t.,;:\'"-')
        special_ratio = special_chars / len(text) if text else 0
        
        if special_ratio > 0.1:
            issues.append("High ratio of special characters")
            score -= 10
        
        level = "excellent" if score >= 90 else "good" if score >= 70 else "fair" if score >= 50 else "poor"
        
        return {
            "score": max(0, score),
            "level": level,
            "issues": issues,
            "metrics": {
                "avg_word_length": round(avg_word_length, 2),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "special_char_ratio": round(special_ratio, 3)
            }
        }
    
    def _extract_txt(self, file_path: Path) -> Dict:
        """Extract from TXT file with analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # Clean text
            cleaned_text = self._clean_text(text)
            
            logger.info(f"Successfully extracted text from {file_path.name}")
            
            return {
                "full_text": cleaned_text,
                "pages": [{
                    "page_num": 1,
                    "text": cleaned_text,
                    "raw_text": text,
                    "length": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                    "structure": self._detect_structure(cleaned_text),
                    "sections": self._extract_sections(cleaned_text)
                }],
                "metadata": {
                    "total_pages": 1,
                    "filename": file_path.name,
                    "title": file_path.stem
                },
                "total_characters": len(cleaned_text),
                "total_words": len(cleaned_text.split()),
                "extraction_quality": self._assess_extraction_quality(cleaned_text)
            }
        except Exception as e:
            logger.error(f"Error reading TXT file {file_path.name}: {str(e)}")
            raise ValueError(f"Error reading file: {str(e)}")

