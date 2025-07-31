"""
Enhanced element classifier for resume-specific categorization.
Moves beyond generic UncategorizedText to specific resume element types.
"""

import re
from typing import Dict, List, Any, Optional
from enum import Enum

from src.models.resume_elements import ElementType

class ResumeElementType(Enum):
    """Enhanced element types specific to resumes."""
    CONTACT_INFO = "contact_info"
    PROFESSIONAL_SUMMARY = "professional_summary"
    JOB_TITLE = "job_title"
    COMPANY_NAME = "company_name"
    EMPLOYMENT_DATE = "employment_date"
    JOB_RESPONSIBILITY = "job_responsibility"
    ACHIEVEMENT = "achievement"
    SKILL_ITEM = "skill_item"
    EDUCATION_DEGREE = "education_degree"
    SCHOOL_NAME = "school_name"
    CERTIFICATION_NAME = "certification_name"
    PROJECT_TITLE = "project_title"
    LANGUAGE_PROFICIENCY = "language_proficiency"
    SECTION_HEADER = "section_header"
    BULLET_POINT = "bullet_point"
    GENERIC_TEXT = "generic_text"

class EnhancedResumeClassifier:
    """Enhanced classifier for resume-specific element categorization."""
    
    def __init__(self):
        self.classification_patterns = self._initialize_classification_patterns()
        self.context_indicators = self._initialize_context_indicators()
        self.skill_keywords = self._load_skill_keywords()
        self.job_title_patterns = self._load_job_title_patterns()
        self.company_indicators = self._load_company_indicators()
    
    def _initialize_classification_patterns(self) -> Dict[ResumeElementType, List[str]]:
        """Initialize patterns for element classification."""
        return {
            ResumeElementType.CONTACT_INFO: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # Phone
                r'linkedin\.com/in/[\w-]+',  # LinkedIn
                r'github\.com/[\w-]+',  # GitHub
                r'\b\d{5}(?:-\d{4})?\b',  # ZIP code
                r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b'  # City, State
            ],
            ResumeElementType.PROFESSIONAL_SUMMARY: [
                r'\b(?:experienced|seasoned|skilled|passionate|dedicated|results-driven|innovative)\b.*\b(?:professional|engineer|developer|manager|analyst)\b',
                r'\b(?:seeking|looking for|interested in)\b.*\b(?:position|role|opportunity)\b',
                r'\byears?\s+of\s+experience\b'
            ],
            ResumeElementType.JOB_TITLE: [
                r'\b(?:Senior|Lead|Principal|Staff|Chief|Head of|Director of|VP of|Manager of)\s+[A-Za-z\s]+\b',
                r'\b[A-Za-z\s]*(?:Engineer|Developer|Programmer|Architect|Manager|Director|Analyst|Consultant|Specialist|Coordinator)\b',
                r'\b(?:Software|Web|Mobile|Data|Systems|Network|Security|DevOps|Full Stack|Frontend|Backend)\s+[A-Za-z\s]*(?:Engineer|Developer)\b'
            ],
            ResumeElementType.COMPANY_NAME: [
                r'\b[A-Z][a-zA-Z\s&.,]*(?:Inc|LLC|Corp|Ltd|Co|Company|Corporation|Technologies|Systems|Solutions|Consulting|Services)\b',
                r'\b(?:at|@)\s+([A-Z][a-zA-Z\s&.,]+)\b'
            ],
            ResumeElementType.EMPLOYMENT_DATE: [
                r'\b(?:\d{1,2}/\d{4}|\w+\s+\d{4})\s*[-–]\s*(?:\d{1,2}/\d{4}|\w+\s+\d{4}|Present|Current)\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
                r'\b\d{4}\s*[-–]\s*(?:\d{4}|Present|Current)\b'
            ],
            ResumeElementType.JOB_RESPONSIBILITY: [
                r'^\s*[•\-\*]\s*(?:Developed|Implemented|Designed|Created|Built|Managed|Led|Coordinated|Collaborated|Responsible for)\b',
                r'^\s*(?:Developed|Implemented|Designed|Created|Built|Managed|Led|Coordinated|Collaborated|Responsible for)\b'
            ],
            ResumeElementType.ACHIEVEMENT: [
                r'^\s*[•\-\*]\s*(?:Achieved|Accomplished|Increased|Decreased|Improved|Reduced|Optimized|Enhanced)\b.*\b(?:\d+%|\$\d+|by \d+)\b',
                r'\b(?:awarded|recognized|achieved|accomplished)\b.*\b(?:award|recognition|achievement|honor)\b'
            ],
            ResumeElementType.SKILL_ITEM: [
                r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|PHP|Go|Rust|Swift|Kotlin|Scala|R|MATLAB)\b',
                r'\b(?:React|Angular|Vue|Django|Flask|Spring|Express|Laravel|Rails|ASP\.NET)\b',
                r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Oracle|SQLite|Cassandra|DynamoDB)\b',
                r'\b(?:AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Jenkins|Git|GitHub)\b'
            ],
            ResumeElementType.EDUCATION_DEGREE: [
                r'\b(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA|Ph\.D\.|Associate)\b.*?(?:in|of)\s+[A-Za-z\s]+',
                r'\b(?:Degree|Diploma|Certificate)\s+in\s+[A-Za-z\s]+'
            ],
            ResumeElementType.SCHOOL_NAME: [
                r'\b(?:[A-Z][a-zA-Z\s]+(?:University|College|Institute|School))\b',
                r'\b(?:University|College|Institute|School)\s+of\s+[A-Za-z\s]+\b'
            ],
            ResumeElementType.CERTIFICATION_NAME: [
                r'\b(?:AWS|Azure|Google|Oracle|Microsoft|Cisco|CompTIA|PMP|Scrum Master|CISSP)\b.*?(?:Certified|Certification|Certificate)',
                r'\b[A-Z][A-Za-z\s]*(?:Certified|Certification|Certificate)\b'
            ],
            ResumeElementType.PROJECT_TITLE: [
                r'\b[A-Z][A-Za-z\s]*(?:Project|System|Application|Platform|Tool|Dashboard|Website|App)\b',
                r'^\s*[•\-\*]\s*[A-Z][A-Za-z\s]*(?:Project|System|Application|Platform)\b'
            ],
            ResumeElementType.LANGUAGE_PROFICIENCY: [
                r'\b(?:English|Spanish|French|German|Chinese|Japanese|Korean|Hindi|Arabic|Portuguese|Russian|Italian)\b\s*[-:]\s*(?:Native|Fluent|Advanced|Intermediate|Basic|Beginner|Professional|Conversational)\b',
                r'\b(?:Native|Fluent|Advanced|Intermediate|Basic|Beginner|Professional|Conversational)\s+(?:in\s+)?(?:English|Spanish|French|German|Chinese|Japanese|Korean|Hindi|Arabic|Portuguese|Russian|Italian)\b'
            ],
            ResumeElementType.SECTION_HEADER: [
                r'^\s*(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT HISTORY)\s*$',
                r'^\s*(?:EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS)\s*$',
                r'^\s*(?:SKILLS|TECHNICAL SKILLS|COMPETENCIES|TECHNOLOGIES)\s*$',
                r'^\s*(?:PROJECTS|PORTFOLIO|NOTABLE PROJECTS)\s*$',
                r'^\s*(?:CERTIFICATIONS|CERTIFICATES|LICENSES)\s*$',
                r'^\s*(?:SUMMARY|OBJECTIVE|PROFILE|OVERVIEW)\s*$'
            ],
            ResumeElementType.BULLET_POINT: [
                r'^\s*[•\-\*\+]\s+.+',
                r'^\s*\d+\.\s+.+'
            ]
        }
    
    def _initialize_context_indicators(self) -> Dict[str, List[str]]:
        """Initialize context indicators for better classification."""
        return {
            'experience_section': ['experience', 'work', 'employment', 'career', 'professional'],
            'education_section': ['education', 'academic', 'qualifications', 'degree'],
            'skills_section': ['skills', 'technical', 'competencies', 'technologies', 'tools'],
            'projects_section': ['projects', 'portfolio', 'work samples'],
            'certifications_section': ['certifications', 'certificates', 'licenses'],
            'summary_section': ['summary', 'objective', 'profile', 'overview'],
            'contact_section': ['contact', 'personal', 'information']
        }
    
    def _load_skill_keywords(self) -> List[str]:
        """Load comprehensive list of technical skills."""
        return [
            # Programming Languages
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB',
            # Web Frameworks
            'React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring', 'Express.js', 'Laravel', 'Ruby on Rails', 'ASP.NET',
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite', 'Cassandra', 'DynamoDB', 'Neo4j',
            # Cloud & DevOps
            'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub', 'GitLab', 'Terraform',
            # Data Science & ML
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Jupyter', 'Apache Spark', 'Hadoop',
            # Mobile Development
            'React Native', 'Flutter', 'iOS', 'Android', 'Xamarin',
            # Other Technologies
            'Node.js', 'GraphQL', 'REST API', 'Microservices', 'Agile', 'Scrum', 'DevOps', 'CI/CD'
        ]
    
    def _load_job_title_patterns(self) -> List[str]:
        """Load patterns for job title recognition."""
        return [
            r'\b(?:Senior|Lead|Principal|Staff|Chief|Head of|Director of|VP of|Manager of)\s+[A-Za-z\s]+\b',
            r'\b[A-Za-z\s]*(?:Engineer|Developer|Programmer|Architect|Manager|Director|Analyst|Consultant|Specialist|Coordinator|Designer|Tester|Administrator)\b',
            r'\b(?:Software|Web|Mobile|Data|Systems|Network|Security|DevOps|Full Stack|Frontend|Backend|Machine Learning|AI)\s+[A-Za-z\s]*(?:Engineer|Developer|Scientist|Analyst)\b'
        ]
    
    def _load_company_indicators(self) -> List[str]:
        """Load indicators for company name recognition."""
        return [
            'Inc', 'LLC', 'Corp', 'Ltd', 'Co', 'Company', 'Corporation', 'Technologies', 'Systems', 'Solutions',
            'Consulting', 'Services', 'Group', 'Holdings', 'Enterprises', 'International', 'Global'
        ]
    
    def classify_element(self, text: str, context: Optional[str] = None) -> ResumeElementType:
        """
        Classify a text element into a resume-specific category.
        
        Args:
            text: The text content to classify
            context: Optional context information (e.g., current section)
            
        Returns:
            ResumeElementType classification
        """
        text_stripped = text.strip()
        
        # Skip empty or very short text
        if not text_stripped or len(text_stripped) < 2:
            return ResumeElementType.GENERIC_TEXT
        
        # Check each classification pattern
        for element_type, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_stripped, re.IGNORECASE | re.MULTILINE):
                    return element_type
        
        # Context-based classification
        if context:
            context_classification = self._classify_by_context(text_stripped, context)
            if context_classification != ResumeElementType.GENERIC_TEXT:
                return context_classification
        
        # Additional heuristic-based classification
        return self._classify_by_heuristics(text_stripped)
    
    def _classify_by_context(self, text: str, context: str) -> ResumeElementType:
        """Classify element based on section context."""
        context_lower = context.lower()
        
        # Experience section context
        if any(indicator in context_lower for indicator in self.context_indicators['experience_section']):
            if self._is_likely_job_title(text):
                return ResumeElementType.JOB_TITLE
            elif self._is_likely_company_name(text):
                return ResumeElementType.COMPANY_NAME
            elif self._is_likely_date_range(text):
                return ResumeElementType.EMPLOYMENT_DATE
            elif text.startswith(('•', '-', '*')) or text.startswith(('Developed', 'Implemented', 'Managed', 'Led')):
                return ResumeElementType.JOB_RESPONSIBILITY
        
        # Education section context
        elif any(indicator in context_lower for indicator in self.context_indicators['education_section']):
            if self._is_likely_degree(text):
                return ResumeElementType.EDUCATION_DEGREE
            elif self._is_likely_school_name(text):
                return ResumeElementType.SCHOOL_NAME
        
        # Skills section context
        elif any(indicator in context_lower for indicator in self.context_indicators['skills_section']):
            if any(skill.lower() in text.lower() for skill in self.skill_keywords):
                return ResumeElementType.SKILL_ITEM
        
        # Summary section context
        elif any(indicator in context_lower for indicator in self.context_indicators['summary_section']):
            return ResumeElementType.PROFESSIONAL_SUMMARY
        
        return ResumeElementType.GENERIC_TEXT
    
    def _classify_by_heuristics(self, text: str) -> ResumeElementType:
        """Classify using heuristic rules."""
        # Check for bullet points
        if re.match(r'^\s*[•\-\*\+]\s+', text) or re.match(r'^\s*\d+\.\s+', text):
            return ResumeElementType.BULLET_POINT
        
        # Check for section headers (all caps, title case)
        if text.isupper() and len(text.split()) <= 4:
            return ResumeElementType.SECTION_HEADER
        
        # Check for contact information
        if '@' in text or re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', text):
            return ResumeElementType.CONTACT_INFO
        
        # Check for skills (contains technical keywords)
        if any(skill.lower() in text.lower() for skill in self.skill_keywords[:20]):  # Check top 20 skills
            return ResumeElementType.SKILL_ITEM
        
        # Check for achievements (contains metrics)
        if re.search(r'\b(?:\d+%|\$\d+|by \d+|increased|decreased|improved|reduced)\b', text, re.IGNORECASE):
            return ResumeElementType.ACHIEVEMENT
        
        return ResumeElementType.GENERIC_TEXT
    
    def _is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        for pattern in self.job_title_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _is_likely_company_name(self, text: str) -> bool:
        """Check if text is likely a company name."""
        # Check for company indicators
        if any(indicator in text for indicator in self.company_indicators):
            return True
        
        # Check for "at Company" pattern
        if re.search(r'\bat\s+[A-Z][a-zA-Z\s&.,]+', text):
            return True
        
        # Check if starts with capital letter and contains business-like words
        if text[0].isupper() and any(word in text.lower() for word in ['technologies', 'systems', 'solutions', 'consulting', 'services']):
            return True
        
        return False
    
    def _is_likely_date_range(self, text: str) -> bool:
        """Check if text is likely a date range."""
        date_patterns = [
            r'\b\d{1,2}/\d{4}\s*[-–]\s*(?:\d{1,2}/\d{4}|Present|Current)\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|Current)\b',
            r'\b\d{4}\s*[-–]\s*(?:\d{4}|Present|Current)\b'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)
    
    def _is_likely_degree(self, text: str) -> bool:
        """Check if text is likely a degree."""
        degree_indicators = ['bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'b.a.', 'm.a.', 'mba', 'ph.d.', 'associate', 'degree', 'diploma']
        return any(indicator in text.lower() for indicator in degree_indicators)
    
    def _is_likely_school_name(self, text: str) -> bool:
        """Check if text is likely a school name."""
        school_indicators = ['university', 'college', 'institute', 'school']
        return any(indicator in text.lower() for indicator in school_indicators)
    
    def classify_elements_batch(self, elements: List[Dict[str, Any]], context: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Classify a batch of elements.
        
        Args:
            elements: List of element dictionaries with 'text' key
            context: Optional context for all elements
            
        Returns:
            List of elements with added 'classification' key
        """
        classified_elements = []
        
        for element in elements:
            text = element.get('text', '')
            classification = self.classify_element(text, context)
            
            classified_element = element.copy()
            classified_element['classification'] = classification.value
            classified_element['confidence'] = self._calculate_confidence(text, classification)
            
            classified_elements.append(classified_element)
        
        return classified_elements
    
    def _calculate_confidence(self, text: str, classification: ResumeElementType) -> float:
        """Calculate confidence score for classification."""
        # Simple confidence calculation based on pattern matches
        if classification == ResumeElementType.GENERIC_TEXT:
            return 0.3
        
        # Check how many patterns match
        patterns = self.classification_patterns.get(classification, [])
        matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        
        if matches == 0:
            return 0.5  # Heuristic-based classification
        elif matches == 1:
            return 0.7
        elif matches >= 2:
            return 0.9
        
        return 0.6
    
    def get_classification_stats(self, classified_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about element classifications."""
        stats = {
            'total_elements': len(classified_elements),
            'classification_counts': {},
            'average_confidence': 0.0,
            'low_confidence_elements': []
        }
        
        total_confidence = 0.0
        
        for element in classified_elements:
            classification = element.get('classification', 'unknown')
            confidence = element.get('confidence', 0.0)
            
            stats['classification_counts'][classification] = stats['classification_counts'].get(classification, 0) + 1
            total_confidence += confidence
            
            if confidence < 0.5:
                stats['low_confidence_elements'].append({
                    'text': element.get('text', '')[:100],  # First 100 chars
                    'classification': classification,
                    'confidence': confidence
                })
        
        if classified_elements:
            stats['average_confidence'] = total_confidence / len(classified_elements)
        
        return stats
