"""
Section-based processor for intelligent resume parsing.
Detects and processes different resume sections with context awareness.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

class ResumeSection(Enum):
    """Enumeration of resume sections."""
    CONTACT = "contact"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    ACHIEVEMENTS = "achievements"
    VOLUNTEER = "volunteer"
    PUBLICATIONS = "publications"
    CONFERENCES = "conferences"
    AFFILIATIONS = "affiliations"
    SECURITY_CLEARANCES = "security_clearances"
    REFERENCES = "references"
    UNKNOWN = "unknown"

class ResumeSectionProcessor:
    """Intelligent section-based resume processor."""
    
    def __init__(self):
        self.section_patterns = self._initialize_section_patterns()
        self.section_keywords = self._initialize_section_keywords()
        self.context_patterns = self._initialize_context_patterns()
    
    def _initialize_section_patterns(self) -> Dict[ResumeSection, List[str]]:
        """Initialize regex patterns for section detection."""
        return {
            ResumeSection.CONTACT: [
                r'\b(?:contact|personal)\s+(?:information|details|info)\b',
                r'\b(?:phone|email|address|linkedin|github)\b'
            ],
            ResumeSection.SUMMARY: [
                r'\b(?:professional\s+)?(?:summary|objective|profile|overview)\b',
                r'\b(?:career\s+)?(?:highlights|goals|statement)\b',
                r'\babout\s+me\b'
            ],
            ResumeSection.EXPERIENCE: [
                r'\b(?:work|professional|employment)\s+experience\b',
                r'\bcareer\s+history\b',
                r'\bwork\s+history\b',
                r'\bprofessional\s+background\b'
            ],
            ResumeSection.EDUCATION: [
                r'\b(?:education|academic)\s+(?:background|qualifications|history)?\b',
                r'\bdegrees?\b',
                r'\buniversity|college|school\b'
            ],
            ResumeSection.SKILLS: [
                r'\b(?:technical\s+)?skills\b',
                r'\bcompetencies\b',
                r'\btechnologies\b',
                r'\btools\s+(?:and\s+)?technologies\b',
                r'\bprogramming\s+languages\b'
            ],
            ResumeSection.PROJECTS: [
                r'\bprojects?\b',
                r'\bportfolio\b',
                r'\bwork\s+samples\b',
                r'\bnotable\s+projects\b'
            ],
            ResumeSection.CERTIFICATIONS: [
                r'\bcertifications?\b',
                r'\bcertificates?\b',
                r'\blicenses?\b',
                r'\bprofessional\s+certifications\b'
            ],
            ResumeSection.LANGUAGES: [
                r'\blanguages?\b',
                r'\blinguistic\s+skills\b',
                r'\bforeign\s+languages\b'
            ],
            ResumeSection.ACHIEVEMENTS: [
                r'\bachievements?\b',
                r'\bawards?\b',
                r'\bhonors?\b',
                r'\baccomplishments?\b',
                r'\brecognitions?\b'
            ],
            ResumeSection.VOLUNTEER: [
                r'\bvolunteer\s+(?:experience|work|activities)\b',
                r'\bcommunity\s+(?:service|involvement)\b',
                r'\bvolunteering\b'
            ],
            ResumeSection.PUBLICATIONS: [
                r'\bpublications?\b',
                r'\bpapers?\b',
                r'\barticles?\b',
                r'\bresearch\s+publications\b'
            ],
            ResumeSection.CONFERENCES: [
                r'\bconferences?\b',
                r'\bpresentations?\b',
                r'\bspeaking\s+engagements\b'
            ],
            ResumeSection.AFFILIATIONS: [
                r'\baffiliations?\b',
                r'\bmemberships?\b',
                r'\bprofessional\s+associations\b'
            ],
            ResumeSection.SECURITY_CLEARANCES: [
                r'\bsecurity\s+clearances?\b',
                r'\bclearance\s+level\b'
            ],
            ResumeSection.REFERENCES: [
                r'\breferences?\b',
                r'\brecommendations?\b',
                r'\bcontact\s+references\b'
            ]
        }
    
    def _initialize_section_keywords(self) -> Dict[ResumeSection, List[str]]:
        """Initialize keyword lists for section content validation."""
        return {
            ResumeSection.CONTACT: [
                'email', 'phone', 'address', 'linkedin', 'github', 'website',
                'portfolio', 'stackoverflow', 'twitter', 'location'
            ],
            ResumeSection.SUMMARY: [
                'experienced', 'professional', 'skilled', 'passionate', 'dedicated',
                'results-driven', 'innovative', 'strategic', 'leadership'
            ],
            ResumeSection.EXPERIENCE: [
                'developed', 'managed', 'led', 'implemented', 'designed', 'created',
                'responsible', 'achieved', 'improved', 'collaborated', 'company',
                'role', 'position', 'team', 'project'
            ],
            ResumeSection.EDUCATION: [
                'university', 'college', 'degree', 'bachelor', 'master', 'phd',
                'graduated', 'gpa', 'coursework', 'thesis', 'honors'
            ],
            ResumeSection.SKILLS: [
                'python', 'java', 'javascript', 'react', 'angular', 'sql',
                'aws', 'docker', 'kubernetes', 'git', 'agile', 'programming',
                'framework', 'database', 'cloud', 'devops'
            ],
            ResumeSection.PROJECTS: [
                'built', 'developed', 'created', 'implemented', 'designed',
                'technologies', 'features', 'application', 'system', 'platform'
            ],
            ResumeSection.CERTIFICATIONS: [
                'certified', 'certification', 'license', 'credential', 'aws',
                'microsoft', 'google', 'oracle', 'cisco', 'comptia'
            ],
            ResumeSection.LANGUAGES: [
                'english', 'spanish', 'french', 'german', 'chinese', 'japanese',
                'fluent', 'native', 'intermediate', 'basic', 'conversational'
            ]
        }
    
    def _initialize_context_patterns(self) -> Dict[str, str]:
        """Initialize context-specific patterns for better extraction."""
        return {
            'date_range': r'\b(?:\d{1,2}/\d{4}|\w+\s+\d{4})\s*[-–]\s*(?:\d{1,2}/\d{4}|\w+\s+\d{4}|Present|Current)\b',
            'job_title_context': r'(?:^|\n)\s*([A-Z][a-zA-Z\s&]+(?:Engineer|Developer|Manager|Director|Analyst|Consultant|Specialist))\s*(?:\n|$)',
            'company_context': r'(?:at|@)\s+([A-Z][a-zA-Z\s&.,]+(?:Inc|LLC|Corp|Ltd|Co|Company)?)',
            'degree_context': r'\b(Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA|Ph\.D\.)\s+(?:of\s+|in\s+)?([A-Za-z\s]+)',
            'skill_context': r'(?:proficient\s+in|experienced\s+with|skilled\s+in|knowledge\s+of)\s+([A-Za-z\s,]+)',
            'achievement_context': r'(?:achieved|accomplished|awarded|recognized)\s+([A-Za-z\s]+)',
            'location_context': r'\b([A-Z][a-z]+,\s*[A-Z]{2}|[A-Z][a-z]+,\s*[A-Z][a-z]+)\b'
        }
    
    def detect_sections(self, text: str) -> Dict[ResumeSection, List[Tuple[int, int, str]]]:
        """
        Detect resume sections in text.
        Returns dict mapping sections to list of (start_pos, end_pos, content) tuples.
        """
        sections = {section: [] for section in ResumeSection}
        lines = text.split('\n')
        
        current_section = ResumeSection.UNKNOWN
        section_start = 0
        section_content = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if line is a section header
            detected_section = self._detect_section_header(line_stripped)
            
            if detected_section != ResumeSection.UNKNOWN:
                # Save previous section
                if current_section != ResumeSection.UNKNOWN and section_content:
                    content = '\n'.join(section_content)
                    sections[current_section].append((section_start, i, content))
                
                # Start new section
                current_section = detected_section
                section_start = i
                section_content = []
            else:
                # Add line to current section
                section_content.append(line_stripped)
        
        # Save final section
        if current_section != ResumeSection.UNKNOWN and section_content:
            content = '\n'.join(section_content)
            sections[current_section].append((section_start, len(lines), content))
        
        return sections
    
    def _detect_section_header(self, line: str) -> ResumeSection:
        """Detect if a line is a section header."""
        line_lower = line.lower()
        
        # Check each section's patterns
        for section, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower, re.IGNORECASE):
                    return section
        
        # Additional heuristics for section detection
        if self._is_likely_section_header(line):
            return self._classify_section_by_keywords(line_lower)
        
        return ResumeSection.UNKNOWN
    
    def _is_likely_section_header(self, line: str) -> bool:
        """Check if line is likely a section header based on formatting."""
        line_stripped = line.strip()
        
        # Check for common header characteristics
        if len(line_stripped) < 3 or len(line_stripped) > 50:
            return False
        
        # All caps
        if line_stripped.isupper():
            return True
        
        # Title case with limited words
        words = line_stripped.split()
        if len(words) <= 4 and all(word[0].isupper() for word in words if word):
            return True
        
        # Contains common section indicators
        section_indicators = ['experience', 'education', 'skills', 'projects', 'summary']
        if any(indicator in line_stripped.lower() for indicator in section_indicators):
            return True
        
        return False
    
    def _classify_section_by_keywords(self, line_lower: str) -> ResumeSection:
        """Classify section based on keywords in the line."""
        for section, keywords in self.section_keywords.items():
            if any(keyword in line_lower for keyword in keywords[:3]):  # Check top 3 keywords
                return section
        
        return ResumeSection.UNKNOWN
    
    def extract_section_content(self, section: ResumeSection, content: str) -> Dict[str, Any]:
        """Extract structured data from a specific section."""
        if section == ResumeSection.CONTACT:
            return self._extract_contact_section(content)
        elif section == ResumeSection.SUMMARY:
            return self._extract_summary_section(content)
        elif section == ResumeSection.EXPERIENCE:
            return self._extract_experience_section(content)
        elif section == ResumeSection.EDUCATION:
            return self._extract_education_section(content)
        elif section == ResumeSection.SKILLS:
            return self._extract_skills_section(content)
        elif section == ResumeSection.PROJECTS:
            return self._extract_projects_section(content)
        elif section == ResumeSection.CERTIFICATIONS:
            return self._extract_certifications_section(content)
        elif section == ResumeSection.LANGUAGES:
            return self._extract_languages_section(content)
        else:
            return {'raw_content': content}
    
    def _extract_contact_section(self, content: str) -> Dict[str, Any]:
        """Extract contact information from contact section."""
        contact_data = {}
        
        # Email extraction
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content, re.IGNORECASE)
        if emails:
            contact_data['email'] = emails[0]
            if len(emails) > 1:
                contact_data['alternateEmail'] = emails[1]
        
        # Phone extraction
        phones = re.findall(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
        if phones:
            contact_data['phone'] = phones[0]
            if len(phones) > 1:
                contact_data['alternatePhone'] = phones[1]
        
        # Social media links
        linkedin = re.findall(r'linkedin\.com/in/[\w-]+', content, re.IGNORECASE)
        if linkedin:
            contact_data['linkedin'] = linkedin[0]
        
        github = re.findall(r'github\.com/[\w-]+', content, re.IGNORECASE)
        if github:
            contact_data['github'] = github[0]
        
        # Location
        locations = re.findall(self.context_patterns['location_context'], content)
        if locations:
            location = locations[0]
            if ',' in location:
                parts = location.split(',')
                contact_data['city'] = parts[0].strip()
                contact_data['state'] = parts[1].strip()
        
        return contact_data
    
    def _extract_summary_section(self, content: str) -> Dict[str, Any]:
        """Extract summary information."""
        return {
            'summary': content.strip(),
            'word_count': len(content.split()),
            'key_phrases': self._extract_key_phrases(content)
        }
    
    def _extract_experience_section(self, content: str) -> Dict[str, Any]:
        """Extract work experience information."""
        experiences = []
        
        # Split by job entries (heuristic: look for job titles followed by companies)
        job_entries = re.split(r'\n(?=[A-Z][a-zA-Z\s]+(?:Engineer|Developer|Manager|Director|Analyst))', content)
        
        for entry in job_entries:
            if not entry.strip():
                continue
            
            experience = {}
            
            # Extract job title (first line typically)
            lines = entry.strip().split('\n')
            if lines:
                potential_title = lines[0].strip()
                if self._is_likely_job_title(potential_title):
                    experience['jobTitle'] = potential_title
            
            # Extract company
            companies = re.findall(self.context_patterns['company_context'], entry, re.IGNORECASE)
            if companies:
                experience['employer'] = companies[0].strip()
            
            # Extract date range
            dates = re.findall(self.context_patterns['date_range'], entry, re.IGNORECASE)
            if dates:
                date_range = dates[0]
                if '-' in date_range or '–' in date_range:
                    parts = re.split(r'[-–]', date_range)
                    if len(parts) == 2:
                        experience['startDate'] = parts[0].strip()
                        experience['endDate'] = parts[1].strip()
                        experience['isCurrent'] = 'present' in parts[1].lower() or 'current' in parts[1].lower()
            
            # Extract responsibilities (remaining content)
            if len(lines) > 1:
                responsibilities = '\n'.join(lines[1:]).strip()
                experience['responsibilities'] = responsibilities
            
            if experience:
                experiences.append(experience)
        
        return {'experiences': experiences}
    
    def _extract_education_section(self, content: str) -> Dict[str, Any]:
        """Extract education information."""
        education_entries = []
        
        # Extract degrees
        degrees = re.findall(self.context_patterns['degree_context'], content, re.IGNORECASE)
        for degree_match in degrees:
            if isinstance(degree_match, tuple) and len(degree_match) >= 2:
                education_entry = {
                    'degreeName': degree_match[0],
                    'fieldOfStudy': degree_match[1].strip()
                }
                education_entries.append(education_entry)
        
        # Extract universities/schools
        universities = re.findall(r'\b(?:[A-Z][a-zA-Z\s]+(?:University|College|Institute|School))\b', content)
        
        # Match universities to degrees (simplified)
        for i, edu_entry in enumerate(education_entries):
            if i < len(universities):
                edu_entry['schoolName'] = universities[i]
        
        # Extract GPA
        gpas = re.findall(r'\bGPA:?\s*(\d\.\d{1,2})\b', content, re.IGNORECASE)
        if gpas and education_entries:
            education_entries[0]['gpa'] = gpas[0]
        
        return {'education': education_entries}
    
    def _extract_skills_section(self, content: str) -> Dict[str, Any]:
        """Extract skills information."""
        skills = []
        
        # Split by common delimiters
        skill_text = re.sub(r'[•\-\*]', ',', content)
        potential_skills = [s.strip() for s in skill_text.split(',') if s.strip()]
        
        for skill in potential_skills:
            if len(skill) > 2 and len(skill) < 50:  # Reasonable skill name length
                skill_entry = {
                    'name': skill,
                    'category': self._categorize_skill(skill),
                    'proficiencyLevel': 'Intermediate'  # Default
                }
                skills.append(skill_entry)
        
        return {'skills': skills}
    
    def _extract_projects_section(self, content: str) -> Dict[str, Any]:
        """Extract projects information."""
        projects = []
        
        # Split by project entries (heuristic: lines starting with project names)
        project_entries = re.split(r'\n(?=[A-Z][a-zA-Z\s]+(?:Project|System|Application|Platform))', content)
        
        for entry in project_entries:
            if not entry.strip():
                continue
            
            lines = entry.strip().split('\n')
            if lines:
                project = {
                    'projectTitle': lines[0].strip(),
                    'description': '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
                }
                
                # Extract technologies
                tech_matches = re.findall(r'(?:using|with|technologies?:?)\s+([A-Za-z\s,]+)', entry, re.IGNORECASE)
                if tech_matches:
                    project['technologiesUsed'] = tech_matches[0].strip()
                
                projects.append(project)
        
        return {'projects': projects}
    
    def _extract_certifications_section(self, content: str) -> Dict[str, Any]:
        """Extract certifications information."""
        certifications = []
        
        # Common certification patterns
        cert_patterns = [
            r'([A-Z][A-Za-z\s]+(?:Certified|Certification|Certificate))',
            r'(AWS|Azure|Google|Microsoft|Oracle|Cisco|CompTIA)\s+([A-Za-z\s]+)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    cert_name = ' '.join(match).strip()
                else:
                    cert_name = match.strip()
                
                certifications.append({
                    'name': cert_name,
                    'certificationType': 'Professional'
                })
        
        return {'certifications': certifications}
    
    def _extract_languages_section(self, content: str) -> Dict[str, Any]:
        """Extract languages information."""
        languages = []
        
        # Language patterns
        lang_pattern = r'\b(English|Spanish|French|German|Chinese|Japanese|Korean|Hindi|Arabic|Portuguese|Russian|Italian)\b'
        prof_pattern = r'\b(Native|Fluent|Advanced|Intermediate|Basic|Beginner|Professional|Conversational)\b'
        
        lang_matches = re.findall(lang_pattern, content, re.IGNORECASE)
        prof_matches = re.findall(prof_pattern, content, re.IGNORECASE)
        
        for i, lang in enumerate(set(lang_matches)):
            lang_entry = {'language': lang}
            
            if i < len(prof_matches):
                lang_entry['proficiency'] = prof_matches[i]
            else:
                lang_entry['proficiency'] = 'Unknown'
            
            languages.append(lang_entry)
        
        return {'languages': languages}
    
    def _is_likely_job_title(self, text: str) -> bool:
        """Check if text is likely a job title."""
        job_indicators = ['engineer', 'developer', 'manager', 'director', 'analyst', 'consultant', 'specialist', 'lead', 'senior', 'principal']
        return any(indicator in text.lower() for indicator in job_indicators)
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill based on its name."""
        skill_lower = skill.lower()
        
        if any(lang in skill_lower for lang in ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'go']):
            return 'Programming Language'
        elif any(fw in skill_lower for fw in ['react', 'angular', 'vue', 'django', 'flask', 'spring']):
            return 'Framework'
        elif any(db in skill_lower for db in ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle']):
            return 'Database'
        elif any(cloud in skill_lower for cloud in ['aws', 'azure', 'gcp', 'docker', 'kubernetes']):
            return 'Cloud/DevOps'
        else:
            return 'Technical'
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple key phrase extraction (can be enhanced with NLP)
        phrases = []
        
        # Look for phrases with specific patterns
        phrase_patterns = [
            r'(?:experienced|skilled|proficient)\s+(?:in|with)\s+([A-Za-z\s]+)',
            r'(?:passionate|dedicated|committed)\s+(?:to|about)\s+([A-Za-z\s]+)',
            r'(?:expertise|background|knowledge)\s+(?:in|with)\s+([A-Za-z\s]+)'
        ]
        
        for pattern in phrase_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend([match.strip() for match in matches])
        
        return phrases[:5]  # Return top 5 phrases
    
    def process_resume_sections(self, text: str) -> Dict[str, Any]:
        """Process entire resume and extract all sections."""
        sections = self.detect_sections(text)
        processed_data = {}
        
        for section, section_data in sections.items():
            if section_data:  # If section was found
                section_content = section_data[0][2]  # Get content from first occurrence
                processed_data[section.value] = self.extract_section_content(section, section_content)
        
        return processed_data
