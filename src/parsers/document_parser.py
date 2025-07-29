"""
Document parser using the unstructured library to extract structured elements.
Handles multiple file formats and converts them into DocumentElement objects.
"""

import io
import tempfile
import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from unstructured.partition.auto import partition
from unstructured.documents.elements import Element

from src.models.resume_elements import (
    DocumentElement,
    ElementType,
    ParsedDocument,
    ResumeSection
)


class DocumentParser:
    """Handles document parsing using the unstructured library."""
    
    def __init__(self):
        """Initialize the document parser."""
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.html', '.htm'}
    
    def parse_document(
        self,
        file_content: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse a document and extract structured elements.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            mime_type: MIME type if available
            
        Returns:
            ParsedDocument with extracted elements
        """
        file_extension = Path(filename).suffix.lower()
        file_type = self._get_file_type(file_extension)
        
        try:
            # Create temporary file for unstructured processing
            with tempfile.NamedTemporaryFile(
                suffix=file_extension,
                delete=False
            ) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Use unstructured to partition the document
                # Use hi_res strategy for PDFs to enable OCR and better text extraction
                if file_extension.lower() == '.pdf':
                    from unstructured.partition.pdf import partition_pdf
                    elements = partition_pdf(
                        filename=temp_file_path,
                        strategy="hi_res",  # High resolution for better OCR
                        infer_table_structure=True,
                        extract_images_in_pdf=False,
                        languages=['eng']
                    )
                else:
                    elements = partition(
                        filename=temp_file_path,
                        strategy="auto",
                        include_page_breaks=True,
                        infer_table_structure=True,
                        chunking_strategy=None  # We'll handle chunking ourselves
                    )
                
                # Convert unstructured elements to our DocumentElement format
                document_elements = self._convert_elements(elements)
                
                # Create parsed document
                parsed_doc = ParsedDocument(
                    filename=filename,
                    file_extension=file_extension,
                    file_type=file_type,
                    total_elements=len(document_elements),
                    grouped_sections=[],  # Will be populated by ContentProcessor
                    parsing_warnings=[]
                )
                
                # Store the elements for processing
                parsed_doc._raw_elements = document_elements
                
                return parsed_doc
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            # Return document with error information
            return ParsedDocument(
                filename=filename,
                file_extension=file_extension,
                file_type=file_type,
                total_elements=0,
                grouped_sections=[],
                parsing_warnings=[f"Parsing failed: {str(e)}"]
            )
    
    def _convert_elements(self, unstructured_elements: List[Element]) -> List[DocumentElement]:
        """
        Convert unstructured library elements to our DocumentElement format.
        
        Args:
            unstructured_elements: Elements from unstructured library
            
        Returns:
            List of DocumentElement objects
        """
        document_elements = []
        
        for element in unstructured_elements:
            try:
                # Map unstructured element types to our ElementType enum
                element_type = self._map_element_type(element.category)
                
                # Extract metadata
                metadata = {}
                if hasattr(element, 'metadata') and element.metadata:
                    metadata = element.metadata.to_dict() if hasattr(element.metadata, 'to_dict') else {}
                    # Remove coordinates from metadata to avoid Pydantic validation errors
                    metadata.pop('coordinates', None)
                
                # Extract page number if available
                page_number = None
                if 'page_number' in metadata:
                    page_number = metadata.get('page_number')
                
                # Extract coordinates if available - handle unstructured coordinate objects
                coordinates = None
                if 'coordinates' in metadata:
                    coord_obj = metadata.get('coordinates')
                    # Skip coordinates to avoid Pydantic validation errors with complex objects
                    # The unstructured library returns complex coordinate objects that don't match our schema
                    coordinates = None
                
                # Create DocumentElement
                doc_element = DocumentElement(
                    element_type=element_type,
                    text=str(element),
                    metadata=metadata,
                    page_number=page_number,
                    coordinates=coordinates
                )
                
                document_elements.append(doc_element)
                
            except Exception as e:
                # Skip problematic elements but log the issue
                continue
        
        return document_elements
    
    def _map_element_type(self, unstructured_category: str) -> ElementType:
        """
        Map unstructured library element categories to our ElementType enum.
        
        Args:
            unstructured_category: Category from unstructured library
            
        Returns:
            Corresponding ElementType
        """
        category_mapping = {
            'Title': ElementType.TITLE,
            'NarrativeText': ElementType.NARRATIVE_TEXT,
            'ListItem': ElementType.LIST_ITEM,
            'Table': ElementType.TABLE,
            'Header': ElementType.HEADER,
            'Footer': ElementType.FOOTER,
            'EmailAddress': ElementType.EMAIL_ADDRESS,
            'Address': ElementType.ADDRESS,
            'PhoneNumber': ElementType.PHONE_NUMBER,
            'UncategorizedText': ElementType.NARRATIVE_TEXT,  # Fallback
            'Text': ElementType.NARRATIVE_TEXT,  # Fallback
        }
        
        return category_mapping.get(unstructured_category, ElementType.NARRATIVE_TEXT)
    
    def _get_file_type(self, extension: str) -> str:
        """
        Get human-readable file type from extension.
        
        Args:
            extension: File extension (e.g., '.pdf')
            
        Returns:
            Human-readable file type
        """
        type_mapping = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document (DOCX)',
            '.doc': 'Word Document (DOC)',
            '.txt': 'Text Document',
            '.html': 'HTML Document',
            '.htm': 'HTML Document'
        }
        
        return type_mapping.get(extension, 'Unknown Document Type')
    
    def get_document_stats(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """
        Get statistics about the parsed document.
        
        Args:
            parsed_doc: Parsed document
            
        Returns:
            Dictionary with document statistics
        """
        element_counts = {}
        total_text_length = 0
        
        for section in parsed_doc.grouped_sections:
            for element in section.elements:
                element_type = element.element_type.value
                element_counts[element_type] = element_counts.get(element_type, 0) + 1
                total_text_length += len(element.text)
        
        return {
            'total_elements': parsed_doc.total_elements,
            'element_type_counts': element_counts,
            'total_text_length': total_text_length,
            'has_warnings': len(parsed_doc.parsing_warnings) > 0,
            'warning_count': len(parsed_doc.parsing_warnings)
        }
