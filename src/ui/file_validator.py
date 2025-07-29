"""
File validation utilities for resume uploads.
Handles file type checking, size validation, and content verification.
"""

import os
import mimetypes
from typing import Tuple, Optional, List
from io import BytesIO

from config.settings import settings, validate_file_extension, validate_file_size, get_file_type_from_extension


class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


class FileValidator:
    """Handles validation of uploaded resume files."""
    
    @staticmethod
    def validate_uploaded_file(
        file_content: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate an uploaded file for resume parsing.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            mime_type: MIME type if available
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check filename
        if not filename or not filename.strip():
            errors.append("Filename is required")
            return False, errors
        
        # Check file extension
        if not validate_file_extension(filename):
            supported_exts = ", ".join(sorted(settings.SUPPORTED_EXTENSIONS))
            errors.append(f"Unsupported file type. Supported formats: {supported_exts}")
        
        # Check file size
        file_size = len(file_content)
        if not validate_file_size(file_size):
            max_mb = settings.MAX_FILE_SIZE_MB
            actual_mb = round(file_size / (1024 * 1024), 2)
            errors.append(f"File too large ({actual_mb}MB). Maximum size: {max_mb}MB")
        
        # Check if file is empty
        if file_size == 0:
            errors.append("File is empty")
        
        # Validate MIME type if provided
        if mime_type and mime_type not in settings.SUPPORTED_MIME_TYPES:
            # Try to guess MIME type from filename
            guessed_type, _ = mimetypes.guess_type(filename)
            if guessed_type not in settings.SUPPORTED_MIME_TYPES:
                errors.append(f"Unsupported MIME type: {mime_type}")
        
        # Basic content validation
        try:
            content_errors = FileValidator._validate_file_content(file_content, filename)
            errors.extend(content_errors)
        except Exception as e:
            errors.append(f"Content validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_file_content(file_content: bytes, filename: str) -> List[str]:
        """
        Perform basic content validation based on file type.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            
        Returns:
            List of validation errors
        """
        errors = []
        ext = os.path.splitext(filename.lower())[1]
        
        try:
            if ext == ".pdf":
                # Check for PDF header
                if not file_content.startswith(b'%PDF-'):
                    errors.append("Invalid PDF file format")
            
            elif ext in [".docx"]:
                # Check for ZIP header (DOCX is a ZIP archive)
                if not file_content.startswith(b'PK'):
                    errors.append("Invalid DOCX file format")
            
            elif ext == ".doc":
                # Check for DOC header
                if not (file_content.startswith(b'\xd0\xcf\x11\xe0') or 
                       file_content.startswith(b'\x0d\x44\x4f\x43')):
                    errors.append("Invalid DOC file format")
            
            elif ext in [".txt"]:
                # Try to decode as text
                try:
                    file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        file_content.decode('latin-1')
                    except UnicodeDecodeError:
                        errors.append("Text file contains invalid characters")
            
            elif ext in [".html", ".htm"]:
                # Basic HTML validation
                try:
                    content_str = file_content.decode('utf-8')
                    if not any(tag in content_str.lower() for tag in ['<html', '<body', '<div', '<p']):
                        errors.append("File does not appear to contain valid HTML")
                except UnicodeDecodeError:
                    errors.append("HTML file contains invalid characters")
        
        except Exception as e:
            errors.append(f"Content validation failed: {str(e)}")
        
        return errors
    
    @staticmethod
    def get_file_info(filename: str, file_size: int) -> dict:
        """
        Get file information for display purposes.
        
        Args:
            filename: Original filename
            file_size: File size in bytes
            
        Returns:
            Dictionary with file information
        """
        ext = os.path.splitext(filename.lower())[1]
        
        return {
            "filename": filename,
            "extension": ext,
            "file_type": get_file_type_from_extension(filename),
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "is_supported": validate_file_extension(filename),
            "is_valid_size": validate_file_size(file_size)
        }
