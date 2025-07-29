"""
Models for document elements extracted by the unstructured library.
These represent the raw parsed elements before processing into the final schema.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ElementType(str, Enum):
    """Types of document elements from unstructured library."""
    TITLE = "Title"
    NARRATIVE_TEXT = "NarrativeText"
    LIST_ITEM = "ListItem"
    TABLE = "Table"
    HEADER = "Header"
    FOOTER = "Footer"
    EMAIL_ADDRESS = "EmailAddress"
    ADDRESS = "Address"
    PHONE_NUMBER = "PhoneNumber"


class DocumentElement(BaseModel):
    """Base class for document elements extracted by unstructured."""
    element_type: ElementType
    text: str
    metadata: Dict[str, Any] = {}
    page_number: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None


class ResumeSection(str, Enum):
    """Identified sections within a resume."""
    CONTACT = "contact"
    SUMMARY = "summary"
    OBJECTIVE = "objective"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    PROJECTS = "projects"
    AWARDS = "awards"
    REFERENCES = "references"
    UNKNOWN = "unknown"


class GroupedElements(BaseModel):
    """Document elements grouped by resume section."""
    section: ResumeSection
    elements: List[DocumentElement]
    confidence: float = 0.0  # Confidence in section classification
    
    @property
    def combined_text(self) -> str:
        """Get all text from elements combined."""
        return "\n".join(element.text for element in self.elements)


class ParsedDocument(BaseModel):
    """Complete parsed document with grouped elements."""
    filename: str
    file_extension: str
    file_type: str
    total_elements: int
    grouped_sections: List[GroupedElements]
    parsing_warnings: List[str] = []
    
    def get_section(self, section: ResumeSection) -> Optional[GroupedElements]:
        """Get elements for a specific section."""
        for grouped in self.grouped_sections:
            if grouped.section == section:
                return grouped
        return None
    
    def get_section_text(self, section: ResumeSection) -> str:
        """Get combined text for a specific section."""
        section_group = self.get_section(section)
        return section_group.combined_text if section_group else ""
