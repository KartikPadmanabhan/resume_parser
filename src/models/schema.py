"""
Pydantic models defining the canonical JSON schema for parsed resumes.
Follows the exact structure specified in the requirements.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import re

def parse_flexible_date(date_str: str) -> Optional[str]:
    """
    Parse various date formats commonly found in resumes.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Standardized date string in YYYY-MM format, or None if unparseable
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip().lower()
    
    # Handle "current" variations
    current_variations = {'current', 'present', 'now', 'ongoing', 'to present', 'till now'}
    if date_str in current_variations:
        return 'current'
    
    # Handle empty/unknown values
    unknown_variations = {'unknown', 'n/a', 'na', '', 'none'}
    if date_str in unknown_variations:
        return None
    
    # Try YYYY-MM-DD format
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
        return parsed_date.strftime('%Y-%m')
    except ValueError:
        pass
    
    # Try YYYY-MM format
    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m')
        return parsed_date.strftime('%Y-%m')
    except ValueError:
        pass
    
    # Try YYYY format only
    try:
        parsed_date = datetime.strptime(date_str, '%Y')
        return parsed_date.strftime('%Y-%m')
    except ValueError:
        pass
    
    # Try month names (e.g., "January 2023", "Jan 2023")
    month_patterns = [
        (r'(\w+)\s+(\d{4})', '%B %Y'),  # January 2023
        (r'(\w{3})\s+(\d{4})', '%b %Y'),  # Jan 2023
    ]
    
    for pattern, format_str in month_patterns:
        match = re.match(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                parsed_date = datetime.strptime(date_str, format_str)
                return parsed_date.strftime('%Y-%m')
            except ValueError:
                continue
    
    # Try season + year (e.g., "Spring 2023")
    season_patterns = [
        (r'spring\s+(\d{4})', 3),   # Spring -> March
        (r'summer\s+(\d{4})', 6),   # Summer -> June
        (r'fall\s+(\d{4})', 9),     # Fall -> September
        (r'autumn\s+(\d{4})', 9),   # Autumn -> September
        (r'winter\s+(\d{4})', 12),  # Winter -> December
    ]
    
    for pattern, month in season_patterns:
        match = re.match(pattern, date_str, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            return f"{year:04d}-{month:02d}"
    
    return None

def validate_date_order(start_date: str, end_date: str) -> bool:
    """
    Validate that start date is before or equal to end date.
    
    Args:
        start_date: Start date in YYYY-MM format
        end_date: End date in YYYY-MM format or 'current'
        
    Returns:
        True if dates are in logical order
    """
    if end_date == 'current':
        return True
    
    try:
        start = datetime.strptime(start_date, '%Y-%m')
        end = datetime.strptime(end_date, '%Y-%m')
        return start <= end
    except ValueError:
        return False  # If we can't parse, let it pass

class Location(BaseModel):
    """Geographic location information."""
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class ContactInfo(BaseModel):
    """Contact information for the resume owner."""
    fullName: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[Location] = None


class Skill(BaseModel):
    """Individual skill with optional metadata."""
    name: str
    category: Optional[str] = None
    experienceInMonths: Optional[int] = None
    lastUsed: Optional[str] = Field(None, description="Date in YYYY-MM format or 'current'")
    isInferred: bool = Field(default=False, description="True if skill was inferred by GPT-4o, False if explicitly mentioned")
    inferredFrom: Optional[str] = Field(None, description="What this skill was inferred from (e.g., 'Streamlit usage')")
    
    @validator('lastUsed')
    def validate_last_used_date(cls, v):
        if v is not None and v.strip() != "":
            parsed_date = parse_flexible_date(v)
            if parsed_date is None:
                raise ValueError('lastUsed must be in a recognizable date format (YYYY-MM, YYYY-MM-DD, month names, etc.) or "current"')
            return parsed_date
        return v


class Education(BaseModel):
    """Educational background entry."""
    schoolName: str
    degreeName: str
    degreeType: str
    location: Optional[Location] = None
    graduationDate: Optional[str] = Field(None, description="Date in YYYY-MM format")
    
    @validator('graduationDate')
    def validate_graduation_date(cls, v):
        if v is not None and v.strip() != "":
            parsed_date = parse_flexible_date(v)
            if parsed_date is None:
                raise ValueError('graduationDate must be in a recognizable date format (YYYY-MM, YYYY-MM-DD, month names, etc.) or empty for unknown graduation date')
            return parsed_date
        return None


class WorkExperience(BaseModel):
    """Work experience entry."""
    jobTitle: str
    employer: str
    location: Optional[Location] = None
    startDate: Optional[str] = Field(None, description="Date in YYYY-MM format or None if unknown")
    endDate: Optional[str] = Field(None, description="Date in YYYY-MM format, 'current', or None if unknown")
    description: str
    
    @validator('startDate')
    def validate_start_date(cls, v):
        # Handle empty strings from GPT responses
        if not v or v.strip() == "":
            return None
        parsed_date = parse_flexible_date(v)
        if parsed_date is None:
            raise ValueError('startDate must be in a recognizable date format (YYYY-MM, YYYY-MM-DD, month names, etc.) or empty for unknown dates')
        return parsed_date
    
    @validator('endDate')
    def validate_end_date(cls, v):
        # Handle empty strings from GPT responses
        if not v or v.strip() == "":
            return None
        parsed_date = parse_flexible_date(v)
        if parsed_date is None:
            raise ValueError('endDate must be in a recognizable date format (YYYY-MM, YYYY-MM-DD, month names, etc.), indicate current employment ("current", "present", etc.), or be empty for unknown dates')
        return parsed_date
    
    @validator('endDate')
    def validate_date_order(cls, v, values):
        """Validate that start date is before end date."""
        # Skip validation if either date is None or missing
        if 'startDate' not in values or values['startDate'] is None or v is None:
            return v
        if v != 'current':
            start_date = values['startDate']
            if not validate_date_order(start_date, v):
                raise ValueError('startDate must be before or equal to endDate')
        return v


class Certification(BaseModel):
    """Professional certification entry."""
    name: str
    issuer: Optional[str] = None
    issueDate: Optional[str] = Field(None, description="Date in YYYY-MM format or None if unknown")
    
    @validator('issueDate')
    def validate_issue_date(cls, v):
        if v is not None and v.strip() != "":
            parsed_date = parse_flexible_date(v)
            if parsed_date is None:
                raise ValueError('issueDate must be in a recognizable date format (YYYY-MM, YYYY-MM-DD, month names, etc.) or empty for unknown issue date')
            return parsed_date
        return None


class ExperienceSummary(BaseModel):
    """Summary of overall work experience."""
    totalMonthsExperience: int
    monthsOfManagementExperience: int
    currentManagementLevel: str
    description: str


class Culture(BaseModel):
    """Cultural and language information."""
    language: str
    country: str
    cultureInfo: str


class ParserMetadata(BaseModel):
    """Metadata about the parsing process."""
    fileType: str
    fileExtension: str
    revisionDate: str
    parserWarnings: List[str] = Field(default_factory=list)
    culture: Optional[Culture] = None


class ResumeSchema(BaseModel):
    """Complete resume schema matching the canonical JSON format."""
    contactInfo: ContactInfo
    summary: str
    skills: List[Skill] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    workExperience: List[WorkExperience] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    experienceSummary: ExperienceSummary
    parserMetadata: ParserMetadata
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True
        use_enum_values = True
