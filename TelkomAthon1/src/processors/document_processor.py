"""
Document processor module for extracting text from various document formats.

This module provides functionality to extract text content from PDF, DOCX, and TXT files.
"""

from io import BytesIO
from typing import Dict, Callable
import PyPDF2
from docx import Document


class DocumentProcessorError(Exception):
    """Base exception for document processor errors"""
    pass


class UnsupportedFormatError(DocumentProcessorError):
    """Raised when an unsupported document format is provided."""
    pass


class EmptyFileError(DocumentProcessorError):
    """Raised when a file is empty or contains no extractable text."""
    pass


class FileSizeError(DocumentProcessorError):
    """Raised when a file exceeds the maximum allowed size."""
    pass


class FileCorruptedError(DocumentProcessorError):
    """Raised when a file is corrupted or cannot be read."""
    pass


class DocumentProcessor:
    """
    Handles extraction of text content from various document formats.
    
    Supports PDF, DOCX, and TXT file formats.
    """
    
    SUPPORTED_FORMATS = {'.pdf', '.docx', '.txt'}
    
    def __init__(self):
        """Initialize the document processor with format handlers."""
        self._format_handlers: Dict[str, Callable[[bytes], str]] = {
            '.pdf': self.extract_text_from_pdf,
            '.docx': self.extract_text_from_docx,
            '.txt': self.extract_text_from_txt,
        }
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_content: The PDF file content as bytes
            
        Returns:
            Extracted text content from the PDF
            
        Raises:
            EmptyFileError: If the PDF contains no extractable text
            FileCorruptedError: If the PDF is corrupted or cannot be read
        """
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            extracted_text = '\n'.join(text_parts)
            
            if not extracted_text.strip():
                raise EmptyFileError("File PDF tidak mengandung teks yang dapat diekstrak")
            
            return extracted_text
            
        except PyPDF2.errors.PdfReadError as e:
            raise FileCorruptedError(f"Gagal membaca file PDF: File mungkin rusak atau terenkripsi")
        except EmptyFileError:
            raise
        except Exception as e:
            raise FileCorruptedError(f"Terjadi kesalahan saat mengekstrak teks dari PDF: {str(e)}")

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """
        Extract text from a DOCX file.
        
        Args:
            file_content: The DOCX file content as bytes
            
        Returns:
            Extracted text content from the DOCX file
            
        Raises:
            EmptyFileError: If the DOCX contains no extractable text
            FileCorruptedError: If the DOCX is corrupted or cannot be read
        """
        try:
            docx_file = BytesIO(file_content)
            doc = Document(docx_file)
            
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            extracted_text = '\n'.join(text_parts)
            
            if not extracted_text.strip():
                raise EmptyFileError("File DOCX tidak mengandung teks yang dapat diekstrak")
            
            return extracted_text
            
        except EmptyFileError:
            raise
        except Exception as e:
            raise FileCorruptedError(f"Terjadi kesalahan saat mengekstrak teks dari DOCX: File mungkin rusak")
    
    def extract_text_from_txt(self, file_content: bytes) -> str:
        """
        Extract text from a TXT file.
        
        Args:
            file_content: The TXT file content as bytes
            
        Returns:
            Extracted text content from the TXT file
            
        Raises:
            EmptyFileError: If the TXT file is empty
            FileCorruptedError: If the TXT file cannot be decoded
        """
        try:
            # Try UTF-8 first, then fall back to other encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    if text.strip():
                        return text
                    elif encoding == encodings[-1]:
                        raise EmptyFileError("File TXT kosong atau tidak mengandung teks")
                    break
                except UnicodeDecodeError:
                    if encoding == encodings[-1]:
                        raise FileCorruptedError(
                            "Tidak dapat membaca file TXT: Format encoding tidak didukung"
                        )
                    continue
            
            return text
            
        except (EmptyFileError, FileCorruptedError):
            raise
        except Exception as e:
            raise FileCorruptedError(f"Terjadi kesalahan saat mengekstrak teks dari TXT: {str(e)}")

    def process_document(self, file_content: bytes, file_type: str) -> str:
        """
        Process a document and extract text based on its file type.
        
        This is the main dispatcher method that routes to the appropriate
        extraction method based on the file type.
        
        Args:
            file_content: The document file content as bytes
            file_type: The file extension (e.g., '.pdf', '.docx', '.txt')
            
        Returns:
            Extracted text content from the document
            
        Raises:
            UnsupportedFormatError: If the file type is not supported
            EmptyFileError: If the file is empty or contains no extractable text
            FileCorruptedError: If the file is corrupted or cannot be read
        """
        # Normalize file type to lowercase and ensure it starts with a dot
        normalized_type = file_type.lower()
        if not normalized_type.startswith('.'):
            normalized_type = f'.{normalized_type}'
        
        if normalized_type not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(
                f"Format file tidak didukung: {file_type}. "
                f"Format yang didukung: PDF, DOCX, TXT"
            )
        
        try:
            handler = self._format_handlers[normalized_type]
            return handler(file_content)
        except (EmptyFileError, FileCorruptedError, UnsupportedFormatError):
            raise
        except Exception as e:
            raise FileCorruptedError(
                f"Terjadi kesalahan tidak terduga saat memproses dokumen: {str(e)}"
            )
    
    def is_format_supported(self, file_type: str) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            file_type: The file extension (e.g., '.pdf', '.docx', '.txt')
            
        Returns:
            True if the format is supported, False otherwise
        """
        normalized_type = file_type.lower()
        if not normalized_type.startswith('.'):
            normalized_type = f'.{normalized_type}'
        
        return normalized_type in self.SUPPORTED_FORMATS
    
    def validate_document_content(self, text: str) -> bool:
        """
        Validate that extracted text is not empty and is meaningful.
        
        Args:
            text: The extracted text to validate
            
        Returns:
            True if the text is valid and meaningful, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Check if text has at least some minimum length (e.g., 10 characters)
        # to ensure it's meaningful content
        return len(text.strip()) >= 10
