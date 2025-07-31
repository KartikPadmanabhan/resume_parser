"""
Enhanced entity extractors for comprehensive resume parsing.
Implements specific extractors for all canonical schema fields.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

class ResumeEntityExtractor:
    """Comprehensive entity extractor for resume parsing."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.keywords = self._initialize_keywords()
    
    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for entity extraction."""
        return {
            # Contact Info patterns
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)[\w-]+',
            'github': r'github\.com/[\w-]+',
            'website': r'(?:https?://)?(?:www\.)?[\w-]+\.[\w.-]+(?:/[\w.-]*)*',
            'stackoverflow': r'stackoverflow\.com/users/\d+/[\w-]+',
            'zipcode': r'\b\d{5}(?:-\d{4})?\b',
            
            # Work Experience patterns
            'job_title': r'\b(?:Senior|Lead|Principal|Staff|Director|VP|Manager|Engineer|Developer|Analyst|Consultant|Specialist|Coordinator|Assistant)\b.*?(?=\n|\r|$)',
            'company': r'(?:at|@)\s+([A-Z][a-zA-Z\s&.,]+(?:Inc|LLC|Corp|Ltd|Co|Company)?)',
            'date_range': r'\b(?:\d{1,2}/\d{4}|\w+\s+\d{4})\s*[-–]\s*(?:\d{1,2}/\d{4}|\w+\s+\d{4}|Present|Current)\b',
            'employment_type': r'\b(?:Full-time|Part-time|Contract|Freelance|Intern|Remote|Hybrid)\b',
            
            # Education patterns
            'degree': r'\b(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA|Ph\.D\.|Associate)\b.*?(?:in|of)\s+([A-Za-z\s]+)',
            'university': r'\b(?:University|College|Institute|School)\s+of\s+\w+|\w+\s+(?:University|College|Institute)\b',
            'gpa': r'\bGPA:?\s*(\d\.\d{1,2})\b',
            
            # Skills patterns
            'programming_languages': r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|PHP|Go|Rust|Swift|Kotlin|Scala|R|MATLAB)\b',
            'frameworks': r'\b(?:React|Angular|Vue|Django|Flask|Spring|Express|Laravel|Rails|ASP\.NET)\b',
            'databases': r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Oracle|SQLite|Cassandra|DynamoDB)\b',
            'cloud_platforms': r'\b(?:AWS|Azure|GCP|Google Cloud|Heroku|DigitalOcean|Vercel)\b',
            
            # Certifications patterns
            'certification': r'\b(?:AWS|Azure|Google|Oracle|Microsoft|Cisco|CompTIA|PMP|Scrum Master|CISSP)\b.*?(?:Certified|Certification)',
            'credential_id': r'\b[A-Z0-9]{6,20}\b',
            
            # Languages patterns
            'language': r'\b(?:English|Spanish|French|German|Chinese|Japanese|Korean|Hindi|Arabic|Portuguese|Russian|Italian|Dutch|Swedish)\b',
            'proficiency': r'\b(?:Native|Fluent|Advanced|Intermediate|Basic|Beginner|Professional|Conversational)\b',
            
            # Metadata patterns
            'years_experience': r'\b(\d+)\+?\s*years?\s*(?:of\s*)?experience\b',
            'salary': r'\$(\d{1,3}(?:,\d{3})*)(?:\.\d{2})?[kK]?',
            'location': r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b|\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b'
        }
    
    def _initialize_keywords(self) -> Dict[str, List[str]]:
        """Initialize keyword lists for entity recognition."""
        return {
            'section_headers': {
                'contact': ['contact', 'personal', 'profile', 'about'],
                'summary': ['summary', 'objective', 'profile', 'overview', 'highlights'],
                'experience': ['experience', 'work', 'employment', 'career', 'professional'],
                'education': ['education', 'academic', 'degree', 'university', 'college'],
                'skills': ['skills', 'technical', 'competencies', 'technologies', 'tools'],
                'projects': ['projects', 'portfolio', 'work samples'],
                'certifications': ['certifications', 'certificates', 'licenses'],
                'achievements': ['achievements', 'awards', 'honors', 'accomplishments'],
                'languages': ['languages', 'linguistic'],
                'volunteer': ['volunteer', 'community', 'service'],
                'publications': ['publications', 'papers', 'articles'],
                'references': ['references', 'recommendations']
            },
            'technical_skills': [
                'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
                'django', 'flask', 'spring', 'express', 'sql', 'mysql', 'postgresql',
                'mongodb', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
                'git', 'github', 'agile', 'scrum', 'devops', 'ci/cd', 'microservices',
                'api', 'rest', 'graphql', 'machine learning', 'ai', 'data science',
                'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'analytical', 'creative', 'adaptable', 'organized', 'detail-oriented'
            ],
            'job_titles': [
                'software engineer', 'developer', 'programmer', 'architect',
                'manager', 'director', 'analyst', 'consultant', 'specialist',
                'coordinator', 'lead', 'senior', 'principal', 'staff'
            ]
        }
    
    def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive contact information."""
        contact_info = {}
        
        # Basic contact extraction
        emails = re.findall(self.patterns['email'], text, re.IGNORECASE)
        phones = re.findall(self.patterns['phone'], text)
        linkedin = re.findall(self.patterns['linkedin'], text, re.IGNORECASE)
        github = re.findall(self.patterns['github'], text, re.IGNORECASE)
        websites = re.findall(self.patterns['website'], text, re.IGNORECASE)
        stackoverflow = re.findall(self.patterns['stackoverflow'], text, re.IGNORECASE)
        locations = re.findall(self.patterns['location'], text)
        zipcodes = re.findall(self.patterns['zipcode'], text)
        
        # Name extraction (first few lines typically contain name)
        lines = text.split('\n')[:5]
        potential_names = []
        for line in lines:
            line = line.strip()
            if len(line.split()) == 2 and line.replace(' ', '').isalpha():
                potential_names.append(line)
        
        # Populate contact info
        if emails:
            contact_info['email'] = emails[0]
            if len(emails) > 1:
                contact_info['alternateEmail'] = emails[1]
        
        if phones:
            contact_info['phone'] = phones[0]
            if len(phones) > 1:
                contact_info['alternatePhone'] = phones[1]
        
        if potential_names:
            full_name = potential_names[0]
            contact_info['fullName'] = full_name
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                contact_info['firstName'] = name_parts[0]
                contact_info['lastName'] = name_parts[-1]
        
        if linkedin:
            contact_info['linkedin'] = linkedin[0]
        if github:
            contact_info['github'] = github[0]
        if websites:
            contact_info['website'] = websites[0]
        if stackoverflow:
            contact_info['stackoverflow'] = stackoverflow[0]
        if locations:
            location = locations[0]
            if ',' in location:
                parts = location.split(',')
                contact_info['city'] = parts[0].strip()
                contact_info['state'] = parts[1].strip()
        if zipcodes:
            contact_info['zipcode'] = zipcodes[0]
        
        return contact_info
    
    def extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience entries."""
        experiences = []
        
        # Find job titles and companies
        job_titles = re.findall(self.patterns['job_title'], text, re.IGNORECASE)
        companies = re.findall(self.patterns['company'], text, re.IGNORECASE)
        date_ranges = re.findall(self.patterns['date_range'], text, re.IGNORECASE)
        employment_types = re.findall(self.patterns['employment_type'], text, re.IGNORECASE)
        
        # Combine information (simplified approach)
        for i, title in enumerate(job_titles[:5]):  # Limit to 5 entries
            experience = {'jobTitle': title.strip()}
            
            if i < len(companies):
                experience['employer'] = companies[i].strip()
            if i < len(date_ranges):
                date_range = date_ranges[i]
                if '-' in date_range or '–' in date_range:
                    parts = re.split(r'[-–]', date_range)
                    if len(parts) == 2:
                        experience['startDate'] = parts[0].strip()
                        experience['endDate'] = parts[1].strip()
                        experience['isCurrent'] = 'present' in parts[1].lower() or 'current' in parts[1].lower()
            if i < len(employment_types):
                experience['employmentType'] = employment_types[i]
            
            experiences.append(experience)
        
        return experiences
    
    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract technical and soft skills."""
        skills = []
        text_lower = text.lower()
        
        # Extract technical skills
        for skill in self.keywords['technical_skills']:
            if skill in text_lower:
                skills.append({
                    'name': skill,
                    'category': 'Technical',
                    'proficiencyLevel': 'Intermediate'  # Default
                })
        
        # Extract programming languages
        prog_langs = re.findall(self.patterns['programming_languages'], text, re.IGNORECASE)
        for lang in set(prog_langs):
            skills.append({
                'name': lang,
                'category': 'Programming Language',
                'proficiencyLevel': 'Intermediate'
            })
        
        # Extract frameworks
        frameworks = re.findall(self.patterns['frameworks'], text, re.IGNORECASE)
        for framework in set(frameworks):
            skills.append({
                'name': framework,
                'category': 'Framework',
                'proficiencyLevel': 'Intermediate'
            })
        
        return skills
    
    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information."""
        education = []
        
        degrees = re.findall(self.patterns['degree'], text, re.IGNORECASE)
        universities = re.findall(self.patterns['university'], text, re.IGNORECASE)
        gpas = re.findall(self.patterns['gpa'], text, re.IGNORECASE)
        
        for i, degree_match in enumerate(degrees):
            if isinstance(degree_match, tuple):
                degree_name = degree_match[0] if degree_match[0] else 'Unknown'
                field_of_study = degree_match[1] if len(degree_match) > 1 else 'Unknown'
            else:
                degree_name = degree_match
                field_of_study = 'Unknown'
            
            edu_entry = {
                'degreeName': degree_name,
                'fieldOfStudy': field_of_study
            }
            
            if i < len(universities):
                edu_entry['schoolName'] = universities[i]
            if i < len(gpas):
                edu_entry['gpa'] = gpas[i]
            
            education.append(edu_entry)
        
        return education
    
    def extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract certifications."""
        certifications = []
        
        cert_matches = re.findall(self.patterns['certification'], text, re.IGNORECASE)
        credential_ids = re.findall(self.patterns['credential_id'], text)
        
        for i, cert in enumerate(cert_matches):
            cert_entry = {'name': cert}
            
            if i < len(credential_ids):
                cert_entry['credentialID'] = credential_ids[i]
            
            certifications.append(cert_entry)
        
        return certifications
    
    def extract_languages(self, text: str) -> List[Dict[str, Any]]:
        """Extract language proficiencies."""
        languages = []
        
        lang_matches = re.findall(self.patterns['language'], text, re.IGNORECASE)
        prof_matches = re.findall(self.patterns['proficiency'], text, re.IGNORECASE)
        
        for i, lang in enumerate(set(lang_matches)):
            lang_entry = {'language': lang}
            
            if i < len(prof_matches):
                lang_entry['proficiency'] = prof_matches[i]
            else:
                lang_entry['proficiency'] = 'Unknown'
            
            languages.append(lang_entry)
        
        return languages
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata information."""
        metadata = {}
        
        # Years of experience
        exp_matches = re.findall(self.patterns['years_experience'], text, re.IGNORECASE)
        if exp_matches:
            years = int(exp_matches[0])
            metadata['totalExperienceInMonths'] = years * 12
        
        # Salary expectations
        salary_matches = re.findall(self.patterns['salary'], text, re.IGNORECASE)
        if salary_matches:
            metadata['expectedSalary'] = salary_matches[0]
        
        # Remote preferences
        remote_keywords = ['remote', 'work from home', 'distributed', 'telecommute']
        for keyword in remote_keywords:
            if keyword in text.lower():
                metadata['remotePreference'] = True
                break
        
        # Processing metadata
        metadata['resumeParsedAt'] = datetime.now().isoformat()
        metadata['resumeLanguage'] = 'English'  # Default
        
        return metadata
    
    def extract_all_entities(self, text: str) -> Dict[str, Any]:
        """Extract all entities from resume text."""
        return {
            'contact_info': self.extract_contact_info(text),
            'work_experience': self.extract_work_experience(text),
            'skills': self.extract_skills(text),
            'education': self.extract_education(text),
            'certifications': self.extract_certifications(text),
            'languages': self.extract_languages(text),
            'metadata': self.extract_metadata(text)
        }
