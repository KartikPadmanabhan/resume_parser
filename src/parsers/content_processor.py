"""
Content processor for grouping document elements into resume sections.
Uses heuristics and pattern matching to identify resume sections.
"""

import re
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import defaultdict

from src.models.resume_elements import (
    DocumentElement,
    ElementType,
    ResumeSection,
    GroupedElements,
    ParsedDocument
)


class ContentProcessor:
    """Processes document elements and groups them into resume sections."""
    
    def __init__(self):
        """Initialize the content processor with section patterns."""
        self.section_patterns = self._build_section_patterns()
        self.contact_patterns = self._build_contact_patterns()
    
    def process_document(self, parsed_doc: ParsedDocument, elements: List[DocumentElement]) -> ParsedDocument:
        """
        Process document elements and group them into resume sections.
        
        Args:
            parsed_doc: Parsed document metadata
            elements: List of document elements to process
            
        Returns:
            Updated ParsedDocument with grouped sections
        """
        try:
            # Group elements by sections
            grouped_sections = self._group_elements_by_section(elements)
            
            # Update the parsed document
            parsed_doc.grouped_sections = grouped_sections
            
            # Add processing statistics
            if not parsed_doc.parsing_warnings:
                parsed_doc.parsing_warnings = []
            
            # Validate sections and add warnings if needed
            self._validate_sections(parsed_doc)
            
            return parsed_doc
            
        except Exception as e:
            parsed_doc.parsing_warnings.append(f"Content processing failed: {str(e)}")
            return parsed_doc
    
    def _group_elements_by_section(self, elements: List[DocumentElement]) -> List[GroupedElements]:
        """
        Group document elements into resume sections using pattern matching.
        
        Args:
            elements: List of document elements
            
        Returns:
            List of grouped elements by section
        """
        sections = defaultdict(list)
        current_section = ResumeSection.UNKNOWN
        
        for element in elements:
            # Check if this element indicates a new section
            detected_section = self._detect_section(element)
            
            if detected_section != ResumeSection.UNKNOWN:
                current_section = detected_section
            
            # Special handling for contact information
            if self._is_contact_element(element):
                sections[ResumeSection.CONTACT].append(element)
            else:
                sections[current_section].append(element)
        
        # Convert to GroupedElements objects
        grouped_sections = []
        for section, section_elements in sections.items():
            if section_elements:  # Only include sections with elements
                confidence = self._calculate_section_confidence(section, section_elements)
                grouped_sections.append(GroupedElements(
                    section=section,
                    elements=section_elements,
                    confidence=confidence
                ))
        
        return grouped_sections
    
    def _detect_section(self, element: DocumentElement) -> ResumeSection:
        """
        Detect which resume section an element belongs to based on patterns.
        
        Args:
            element: Document element to analyze
            
        Returns:
            Detected resume section
        """
        text = element.text.lower().strip()
        
        # Consider titles, headers, and narrative text elements for section detection
        # Many resumes use Text elements (mapped to NARRATIVE_TEXT) for section headers
        valid_types = [ElementType.TITLE, ElementType.HEADER, ElementType.NARRATIVE_TEXT]
        
        if element.element_type not in valid_types:
            return ResumeSection.UNKNOWN
        
        # For NARRATIVE_TEXT elements, only consider short ones that could be headers
        # This filters out long paragraphs but keeps section headers
        if element.element_type == ElementType.NARRATIVE_TEXT and len(text) > 50:
            return ResumeSection.UNKNOWN
        
        # Check against section patterns
        for section, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return section
        
        return ResumeSection.UNKNOWN
    
    def _is_contact_element(self, element: DocumentElement) -> bool:
        """
        Check if an element contains contact information.
        
        Args:
            element: Document element to check
            
        Returns:
            True if element contains contact info
        """
        # Direct element types
        if element.element_type in [ElementType.EMAIL_ADDRESS, ElementType.PHONE_NUMBER, ElementType.ADDRESS]:
            return True
        
        text = element.text
        
        # Check for contact patterns
        for pattern in self.contact_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _calculate_section_confidence(self, section: ResumeSection, elements: List[DocumentElement]) -> float:
        """
        Calculate confidence score for section classification.
        
        Args:
            section: Resume section
            elements: Elements in the section
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not elements:
            return 0.0
        
        # Base confidence
        confidence = 0.5
        
        # Boost confidence for sections with clear headers
        has_header = any(
            elem.element_type in [ElementType.TITLE, ElementType.HEADER]
            for elem in elements
        )
        if has_header:
            confidence += 0.3
        
        # Boost confidence for contact section with structured data
        if section == ResumeSection.CONTACT:
            has_structured_contact = any(
                elem.element_type in [ElementType.EMAIL_ADDRESS, ElementType.PHONE_NUMBER]
                for elem in elements
            )
            if has_structured_contact:
                confidence += 0.2
        
        # Boost confidence for sections with appropriate content types
        if section == ResumeSection.SKILLS:
            has_lists = any(elem.element_type == ElementType.LIST_ITEM for elem in elements)
            if has_lists:
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _build_section_patterns(self) -> Dict[ResumeSection, List[str]]:
        """
        Build regex patterns for detecting resume sections.
        
        Returns:
            Dictionary mapping sections to regex patterns
        """
        return {
            ResumeSection.CONTACT: [
                r'^contact\s*(information|info|details)?$',
                r'^personal\s*(information|info|details)$',
                r'^contact\s*me$'
            ],
            ResumeSection.SUMMARY: [
                r'^(professional\s*)?summary$',
                r'^(career\s*)?summary$',
                r'^profile$',
                r'^overview$',
                r'^about\s*(me)?$',
                r'^executive\s*summary$'
            ],
            ResumeSection.OBJECTIVE: [
                r'^(career\s*)?objective$',
                r'^goal$',
                r'^career\s*goal$'
            ],
            ResumeSection.SKILLS: [
                r'^(technical\s*)?skills$',
                r'^core\s*competencies$',
                r'^competencies$',
                r'^expertise$',
                r'^technologies$',
                r'^programming\s*languages$',
                r'^tools\s*(and\s*technologies)?$'
            ],
            ResumeSection.EXPERIENCE: [
                r'^(work\s*|professional\s*)?experience$',
                r'^employment\s*history$',
                r'^career\s*history$',
                r'^work\s*history$',
                r'^professional\s*background$'
            ],
            ResumeSection.EDUCATION: [
                r'^education$',
                r'^academic\s*background$',
                r'^educational\s*background$',
                r'^qualifications$',
                r'^academic\s*qualifications$'
            ],
            ResumeSection.CERTIFICATIONS: [
                r'^certifications?$',
                r'^certificates?$',
                r'^professional\s*certifications?$',
                r'^licenses?\s*(and\s*certifications?)?$'
            ],
            ResumeSection.PROJECTS: [
                r'^projects?$',
                r'^key\s*projects?$',
                r'^notable\s*projects?$',
                r'^selected\s*projects?$'
            ],
            ResumeSection.AWARDS: [
                r'^awards?$',
                r'^honors?\s*(and\s*awards?)?$',
                r'^achievements?$',
                r'^recognition$'
            ],
            ResumeSection.REFERENCES: [
                r'^references?$',
                r'^professional\s*references?$',
                r'^references?\s*available\s*upon\s*request$'
            ]
        }
    
    def _build_contact_patterns(self) -> List[str]:
        """
        Build regex patterns for detecting contact information.
        
        Returns:
            List of regex patterns for contact info
        """
        return [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone (US format)
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',  # Phone (US format with parentheses)
            r'\+\d{1,3}[-.\s]?\d{1,14}',  # International phone
            r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd)',  # Address
            r'\b(linkedin\.com/in/|github\.com/|twitter\.com/)',  # Social profiles
        ]
    
    def _validate_sections(self, parsed_doc: ParsedDocument) -> None:
        """
        Validate grouped sections and add warnings for missing critical sections.
        
        Args:
            parsed_doc: Parsed document to validate
        """
        section_names = {section.section for section in parsed_doc.grouped_sections}
        
        # Check for critical sections
        if ResumeSection.CONTACT not in section_names:
            parsed_doc.parsing_warnings.append("No contact information section detected")
        
        if ResumeSection.EXPERIENCE not in section_names:
            parsed_doc.parsing_warnings.append("No work experience section detected")
        
        # Check for low confidence sections
        low_confidence_sections = [
            section for section in parsed_doc.grouped_sections
            if section.confidence < 0.6
        ]
        
        if low_confidence_sections:
            section_names = [section.section.value for section in low_confidence_sections]
            parsed_doc.parsing_warnings.append(
                f"Low confidence in section classification: {', '.join(section_names)}"
            )
    
    def get_section_summary(self, grouped_sections: List[GroupedElements]) -> Dict[str, Any]:
        """
        Get summary statistics for grouped sections.
        
        Args:
            grouped_sections: List of grouped elements
            
        Returns:
            Dictionary with section statistics
        """
        summary = {
            'total_sections': len(grouped_sections),
            'sections_found': [],
            'element_counts': {},
            'average_confidence': 0.0
        }
        
        total_confidence = 0.0
        
        for section_group in grouped_sections:
            section_name = section_group.section.value
            summary['sections_found'].append(section_name)
            summary['element_counts'][section_name] = len(section_group.elements)
            total_confidence += section_group.confidence
        
        if grouped_sections:
            summary['average_confidence'] = total_confidence / len(grouped_sections)
        
        return summary
