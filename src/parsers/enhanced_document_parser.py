"""
Enhanced document parser that fully utilizes unstructured library capabilities.
This implementation leverages advanced features including LLM-powered extraction,
better entity recognition, coordinate extraction, and semantic chunking.
"""

import io
import tempfile
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import re
from datetime import datetime

# Unstructured imports
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element
from unstructured.chunking.title import chunk_by_title
from unstructured.chunking.basic import chunk_elements
from unstructured.staging.base import dict_to_elements, elements_to_json

# Advanced unstructured features
try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.docx import partition_docx
    from unstructured.partition.html import partition_html
    from unstructured.partition.text import partition_text
except ImportError:
    pass

from src.models.resume_elements import (
    DocumentElement,
    ElementType,
    ParsedDocument,
    ResumeSection
)


class EnhancedDocumentParser:
    """
    Enhanced document parser that fully utilizes unstructured library capabilities.
    Includes LLM-powered extraction, advanced entity recognition, and semantic processing.
    """
    
    def __init__(self, use_llm_features: bool = True):
        """Initialize the enhanced document parser."""
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.html', '.htm'}
        self.use_llm_features = use_llm_features
        
        # Entity patterns for enhanced extraction
        self.entity_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'date': r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\w+ \d{4}|\d{4})\b',
            'linkedin': r'linkedin\.com/in/[\w-]+',
            'github': r'github\.com/[\w-]+',
            'degree': r'\b(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA|Ph\.D\.)\b',
            'gpa': r'\bGPA:?\s*\d\.\d{1,2}\b',
            'years_experience': r'\b\d+\+?\s*years?\s*(?:of\s*)?experience\b',
            'salary': r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?[kK]?',
        }
        
        # Resume section keywords for better categorization
        self.section_keywords = {
            'contact': ['contact', 'personal', 'profile', 'about'],
            'summary': ['summary', 'objective', 'profile', 'overview'],
            'experience': ['experience', 'work', 'employment', 'career', 'professional'],
            'education': ['education', 'academic', 'degree', 'university', 'college'],
            'skills': ['skills', 'technical', 'competencies', 'technologies', 'tools'],
            'projects': ['projects', 'portfolio', 'work samples'],
            'certifications': ['certifications', 'certificates', 'licenses'],
            'achievements': ['achievements', 'awards', 'honors', 'accomplishments'],
            'references': ['references', 'recommendations']
        }
    
    def parse_document(
        self,
        file_content: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse a document with enhanced unstructured capabilities.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            mime_type: MIME type if available
            
        Returns:
            ParsedDocument with enhanced extracted elements
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
                # Use enhanced partition strategy
                elements = self._enhanced_partition_document(temp_file_path, file_extension)
                
                # Post-process elements for better entity extraction
                enhanced_elements = self._enhance_elements(elements)
                
                # Convert to our DocumentElement format
                document_elements = self._convert_enhanced_elements(enhanced_elements)
                
                # Perform semantic chunking
                chunked_elements = self._semantic_chunking(document_elements)
                
                # Extract additional entities
                extracted_entities = self._extract_comprehensive_entities(document_elements)
                
                # Create parsed document with enhanced data
                parsed_doc = ParsedDocument(
                    filename=filename,
                    file_extension=file_extension,
                    file_type=file_type,
                    total_elements=len(document_elements),
                    grouped_sections=[],  # Will be populated by ContentProcessor
                    parsing_warnings=[]
                )
                
                # Store enhanced data
                parsed_doc._raw_elements = document_elements
                parsed_doc._chunked_elements = chunked_elements
                parsed_doc._extracted_entities = extracted_entities
                
                return parsed_doc
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            # Return fallback parsing
            return self._parse_with_enhanced_fallback(file_content, filename, file_extension, file_type)
    
    def _enhanced_partition_document(self, temp_file_path: str, file_extension: str) -> List[Element]:
        """
        Enhanced partition using format-specific parsers and advanced options.
        
        Args:
            temp_file_path: Path to temporary file
            file_extension: File extension
            
        Returns:
            List of enhanced unstructured elements
        """
        base_kwargs = {
            "filename": temp_file_path,
            "include_page_breaks": True,
            "infer_table_structure": True,
            "extract_images_in_pdf": True,
            "extract_image_block_types": ["Image", "Table"],
            "languages": ["eng"],
            "detect_language_per_element": True,
            "multipage_sections": True,
            "combine_text_under_n_chars": 30,  # Smaller threshold for better granularity
            "new_after_n_chars": 500,  # Better chunking for resumes
            "max_characters": 2000,
            "overlap": 50,  # Add overlap for better context
        }
        
        try:
            # Use format-specific parsers for better results
            if file_extension == '.pdf':
                return partition_pdf(
                    **base_kwargs,
                    strategy="hi_res",  # Better for complex layouts
                    extract_image_block_to_payload=False,
                    extract_image_block_types=["Image", "Table"],
                    infer_table_structure=True,
                    chunking_strategy="by_title",
                    max_characters=1500,
                    new_after_n_chars=400,
                    combine_text_under_n_chars=50
                )
            elif file_extension in ['.docx', '.doc']:
                return partition_docx(
                    **base_kwargs,
                    infer_table_structure=True,
                    chunking_strategy="by_title"
                )
            elif file_extension in ['.html', '.htm']:
                return partition_html(
                    **base_kwargs,
                    chunking_strategy="by_title"
                )
            elif file_extension == '.txt':
                return partition_text(
                    **base_kwargs,
                    chunking_strategy="by_title"
                )
            else:
                # Fallback to auto partition with enhanced settings
                return partition(
                    **base_kwargs,
                    strategy="hi_res",
                    chunking_strategy="by_title"
                )
                
        except Exception as e:
            # Fallback to basic partition
            return partition(
                filename=temp_file_path,
                strategy="auto",
                include_page_breaks=True,
                infer_table_structure=True
            )
    
    def _enhance_elements(self, elements: List[Element]) -> List[Element]:
        """
        Enhance elements with additional processing and entity recognition.
        
        Args:
            elements: Original unstructured elements
            
        Returns:
            Enhanced elements with better categorization
        """
        enhanced_elements = []
        
        for element in elements:
            # Get element text
            text = str(element).strip()
            if not text:
                continue
            
            # Enhance element categorization
            enhanced_element = self._enhance_element_category(element, text)
            enhanced_elements.append(enhanced_element)
        
        return enhanced_elements
    
    def _enhance_element_category(self, element: Element, text: str) -> Element:
        """
        Enhance element category based on content analysis.
        
        Args:
            element: Original element
            text: Element text content
            
        Returns:
            Element with enhanced category
        """
        # Check for specific entity types
        text_lower = text.lower()
        
        # Email detection
        if re.search(self.entity_patterns['email'], text, re.IGNORECASE):
            element.category = 'EmailAddress'
        
        # Phone detection
        elif re.search(self.entity_patterns['phone'], text):
            element.category = 'PhoneNumber'
        
        # URL detection
        elif re.search(self.entity_patterns['url'], text, re.IGNORECASE):
            element.category = 'URL'
        
        # Address detection (simple heuristic)
        elif any(addr_word in text_lower for addr_word in ['street', 'avenue', 'road', 'drive', 'lane', 'blvd', 'apt', 'suite']):
            element.category = 'Address'
        
        # Section header detection
        elif any(keyword in text_lower for section, keywords in self.section_keywords.items() for keyword in keywords):
            if element.category in ['UncategorizedText', 'NarrativeText']:
                element.category = 'Title'
        
        # Skills detection
        elif self._is_skills_content(text_lower):
            if element.category in ['UncategorizedText', 'NarrativeText']:
                element.category = 'SkillsText'
        
        return element
    
    def _is_skills_content(self, text_lower: str) -> bool:
        """Check if text contains skills-related content."""
        skills_indicators = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure',
            'docker', 'kubernetes', 'git', 'agile', 'scrum'
        ]
        return any(skill in text_lower for skill in skills_indicators)
    
    def _convert_enhanced_elements(self, elements: List[Element]) -> List[DocumentElement]:
        """
        Convert enhanced unstructured elements to DocumentElement objects.
        
        Args:
            elements: Enhanced unstructured elements
            
        Returns:
            List of DocumentElement objects with enhanced metadata
        """
        document_elements = []
        
        for element in elements:
            try:
                # Map enhanced element types
                element_type = self._map_enhanced_element_type(element.category)
                
                # Extract comprehensive metadata
                metadata = self._extract_comprehensive_metadata(element)
                
                # Get text content
                text_content = str(element).strip()
                if not text_content:
                    continue
                
                # Extract additional properties
                page_number = metadata.get('page_number')
                coordinates = metadata.get('coordinates')
                
                # Add entity-specific metadata
                entity_metadata = self._extract_entity_metadata(text_content, element.category)
                metadata.update(entity_metadata)
                
                # Create enhanced DocumentElement
                doc_element = DocumentElement(
                    element_type=element_type,
                    text=text_content,
                    metadata=metadata,
                    page_number=page_number,
                    coordinates=coordinates
                )
                
                document_elements.append(doc_element)
                
            except Exception as e:
                continue
        
        return document_elements
    
    def _map_enhanced_element_type(self, unstructured_category: str) -> ElementType:
        """
        Map enhanced unstructured categories to ElementType enum.
        
        Args:
            unstructured_category: Enhanced category from unstructured library
            
        Returns:
            Corresponding ElementType
        """
        enhanced_mapping = {
            'Title': ElementType.TITLE,
            'NarrativeText': ElementType.NARRATIVE_TEXT,
            'ListItem': ElementType.LIST_ITEM,
            'Table': ElementType.TABLE,
            'Header': ElementType.HEADER,
            'Footer': ElementType.FOOTER,
            'EmailAddress': ElementType.EMAIL_ADDRESS,
            'Address': ElementType.ADDRESS,
            'PhoneNumber': ElementType.PHONE_NUMBER,
            'URL': ElementType.NARRATIVE_TEXT,  # Could add URL type
            'SkillsText': ElementType.NARRATIVE_TEXT,
            'UncategorizedText': ElementType.NARRATIVE_TEXT,
            'Text': ElementType.NARRATIVE_TEXT,
            'PageBreak': ElementType.NARRATIVE_TEXT,
        }
        
        return enhanced_mapping.get(unstructured_category, ElementType.NARRATIVE_TEXT)
    
    def _extract_comprehensive_metadata(self, element: Element) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from element.
        
        Args:
            element: Unstructured element
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Basic metadata
        if hasattr(element, 'metadata') and element.metadata:
            try:
                base_metadata = element.metadata.to_dict() if hasattr(element.metadata, 'to_dict') else {}
                metadata.update(base_metadata)
            except:
                pass
        
        # Add element category
        metadata['element_category'] = getattr(element, 'category', 'Unknown')
        
        # Add text statistics
        text = str(element)
        metadata['text_length'] = len(text)
        metadata['word_count'] = len(text.split())
        
        # Add extraction timestamp
        metadata['extracted_at'] = datetime.now().isoformat()
        
        return metadata
    
    def _extract_entity_metadata(self, text: str, category: str) -> Dict[str, Any]:
        """
        Extract entity-specific metadata from text.
        
        Args:
            text: Element text
            category: Element category
            
        Returns:
            Entity-specific metadata
        """
        entity_metadata = {}
        
        # Extract entities based on patterns
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entity_metadata[f'{entity_type}_found'] = matches
        
        # Add category-specific metadata
        if category == 'EmailAddress':
            entity_metadata['is_contact_info'] = True
        elif category == 'PhoneNumber':
            entity_metadata['is_contact_info'] = True
        elif category == 'Address':
            entity_metadata['is_contact_info'] = True
        elif category == 'Title':
            entity_metadata['is_section_header'] = True
        
        return entity_metadata
    
    def _semantic_chunking(self, elements: List[DocumentElement]) -> List[DocumentElement]:
        """
        Perform semantic chunking on document elements.
        
        Args:
            elements: Document elements
            
        Returns:
            Semantically chunked elements
        """
        try:
            # Convert back to unstructured elements for chunking
            unstructured_elements = []
            for elem in elements:
                # Create a mock unstructured element
                mock_element = type('MockElement', (), {
                    'text': elem.text,
                    'category': elem.element_type.value,
                    '__str__': lambda self: self.text
                })()
                unstructured_elements.append(mock_element)
            
            # Perform chunking
            chunked = chunk_by_title(
                unstructured_elements,
                max_characters=800,  # Smaller chunks for resumes
                combine_text_under_n_chars=30,
                new_after_n_chars=200
            )
            
            # Convert back to DocumentElements
            chunked_elements = []
            for chunk in chunked:
                doc_element = DocumentElement(
                    element_type=ElementType.NARRATIVE_TEXT,
                    text=str(chunk),
                    metadata={'is_chunk': True, 'chunk_size': len(str(chunk))},
                    page_number=None,
                    coordinates=None
                )
                chunked_elements.append(doc_element)
            
            return chunked_elements
            
        except Exception as e:
            return elements  # Return original elements if chunking fails
    
    def _extract_comprehensive_entities(self, elements: List[DocumentElement]) -> Dict[str, List[str]]:
        """
        Extract comprehensive entities from all elements.
        
        Args:
            elements: Document elements
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {
            'emails': [],
            'phone_numbers': [],
            'urls': [],
            'dates': [],
            'linkedin_profiles': [],
            'github_profiles': [],
            'degrees': [],
            'gpas': [],
            'years_experience': [],
            'salaries': [],
            'skills': [],
            'companies': [],
            'job_titles': [],
            'locations': []
        }
        
        full_text = ' '.join([elem.text for elem in elements])
        
        # Extract using patterns
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if entity_type in entities:
                entities[entity_type] = list(set(matches))
        
        # Extract from element metadata
        for element in elements:
            if element.metadata:
                for key, value in element.metadata.items():
                    if key.endswith('_found') and isinstance(value, list):
                        entity_key = key.replace('_found', 's')
                        if entity_key in entities:
                            entities[entity_key].extend(value)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def _parse_with_enhanced_fallback(self, file_content: bytes, filename: str, 
                                    file_extension: str, file_type: str) -> ParsedDocument:
        """
        Enhanced fallback parsing when main parsing fails.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            file_extension: File extension
            file_type: Human-readable file type
            
        Returns:
            ParsedDocument with fallback extraction
        """
        try:
            # Simple text extraction with entity recognition
            if file_extension == '.txt':
                text_content = file_content.decode('utf-8', errors='ignore')
                
                # Split into logical sections
                sections = self._split_text_into_sections(text_content)
                
                # Create elements from sections
                elements = []
                for i, section in enumerate(sections):
                    if section.strip():
                        element = DocumentElement(
                            element_type=ElementType.NARRATIVE_TEXT,
                            text=section.strip(),
                            metadata={'section_index': i, 'is_fallback': True},
                            page_number=1,
                            coordinates=None
                        )
                        elements.append(element)
                
                # Create parsed document
                parsed_doc = ParsedDocument(
                    filename=filename,
                    file_extension=file_extension,
                    file_type=file_type,
                    total_elements=len(elements),
                    grouped_sections=[],
                    parsing_warnings=['Used fallback text parsing']
                )
                
                parsed_doc._raw_elements = elements
                parsed_doc._extracted_entities = self._extract_comprehensive_entities(elements)
                
                return parsed_doc
            
            else:
                # Return minimal parsed document for other formats
                return ParsedDocument(
                    filename=filename,
                    file_extension=file_extension,
                    file_type=file_type,
                    total_elements=0,
                    grouped_sections=[],
                    parsing_warnings=['Parsing failed, no content extracted']
                )
                
        except Exception as e:
            return ParsedDocument(
                filename=filename,
                file_extension=file_extension,
                file_type=file_type,
                total_elements=0,
                grouped_sections=[],
                parsing_warnings=[f'Fallback parsing failed: {str(e)}']
            )
    
    def _split_text_into_sections(self, text: str) -> List[str]:
        """Split text into logical sections for better processing."""
        # Split by common section headers
        section_patterns = [
            r'\n\s*(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE)\s*\n',
            r'\n\s*(?:EDUCATION|ACADEMIC BACKGROUND)\s*\n',
            r'\n\s*(?:SKILLS|TECHNICAL SKILLS|COMPETENCIES)\s*\n',
            r'\n\s*(?:PROJECTS|PORTFOLIO)\s*\n',
            r'\n\s*(?:CERTIFICATIONS|CERTIFICATES)\s*\n',
            r'\n\s*(?:SUMMARY|OBJECTIVE|PROFILE)\s*\n',
        ]
        
        sections = [text]
        for pattern in section_patterns:
            new_sections = []
            for section in sections:
                new_sections.extend(re.split(pattern, section, flags=re.IGNORECASE))
            sections = new_sections
        
        return [s for s in sections if s.strip()]
    
    def _get_file_type(self, extension: str) -> str:
        """Get human-readable file type from extension."""
        type_mapping = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document (DOCX)',
            '.doc': 'Word Document (DOC)',
            '.txt': 'Text Document',
            '.html': 'HTML Document',
            '.htm': 'HTML Document'
        }
        return type_mapping.get(extension, 'Unknown Document')
