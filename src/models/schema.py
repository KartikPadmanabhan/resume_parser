"""
Pydantic models defining the canonical JSON schema for parsed resumes.
Follows the exact structure specified in the requirements.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


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
    lastUsed: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    isInferred: bool = Field(default=False, description="True if skill was inferred by GPT-4o, False if explicitly mentioned")
    inferredFrom: Optional[str] = Field(None, description="What this skill was inferred from (e.g., 'Streamlit usage')")
    
    @validator('lastUsed')
    def validate_last_used_date(cls, v):
        if v is not None and v.strip() != "":
            # Handle "current" as a valid value for ongoing skill usage
            if v.lower() == "current":
                return "current"
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('lastUsed must be in YYYY-MM-DD format or "current"')
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
        # Handle empty strings and None values
        if v is None or v == '' or v.strip() == '':
            return None
        
        # Try YYYY-MM format first
        try:
            datetime.strptime(v, '%Y-%m')
            return v
        except ValueError:
            pass
        
        # Try YYYY-MM-DD format and convert to YYYY-MM
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m')
        except ValueError:
            raise ValueError('graduationDate must be in YYYY-MM or YYYY-MM-DD format, or empty for unknown graduation date')
        
        return v


class WorkExperience(BaseModel):
    """Work experience entry."""
    jobTitle: str
    employer: str
    location: Optional[Location] = None
    startDate: str = Field(description="Date in YYYY-MM format")
    endDate: str = Field(description="Date in YYYY-MM format or 'current'")
    description: str
    
    @validator('startDate')
    def validate_start_date(cls, v):
        # Try YYYY-MM format first
        try:
            datetime.strptime(v, '%Y-%m')
            return v
        except ValueError:
            pass
        
        # Try YYYY-MM-DD format and convert to YYYY-MM
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m')
        except ValueError:
            raise ValueError('startDate must be in YYYY-MM or YYYY-MM-DD format')
        
        return v
    
    @validator('endDate')
    def validate_end_date(cls, v):
        # Handle common variations of "current" employment
        current_variations = {'current', 'present', 'now', 'ongoing'}
        if v.lower() in current_variations:
            return 'current'  # Normalize to 'current'
        
        # Validate date format - try YYYY-MM first
        try:
            datetime.strptime(v, '%Y-%m')
            return v
        except ValueError:
            pass
        
        # Try YYYY-MM-DD format and convert to YYYY-MM
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m')
        except ValueError:
            raise ValueError('endDate must be in YYYY-MM or YYYY-MM-DD format, or indicate current employment ("current", "present", etc.)')
        return v


class Certification(BaseModel):
    """Professional certification entry."""
    name: str
    issuer: Optional[str] = None
    issueDate: Optional[str] = Field(None, description="Date in YYYY-MM format or None if unknown")
    
    @validator('issueDate')
    def validate_issue_date(cls, v):
        # Handle empty strings and None values
        if v is None or v == '' or v.strip() == '':
            return None
        
        # Try YYYY-MM format first
        try:
            datetime.strptime(v, '%Y-%m')
            return v
        except ValueError:
            pass
        
        # Try YYYY-MM-DD format and convert to YYYY-MM
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')
            return date_obj.strftime('%Y-%m')
        except ValueError:
            raise ValueError('issueDate must be in YYYY-MM or YYYY-MM-DD format, or empty for unknown issue date')
        return v


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
