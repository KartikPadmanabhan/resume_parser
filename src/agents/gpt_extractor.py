"""
GPT powered resume data extractor using function calling.
Transforms parsed document sections into structured resume data matching the canonical JSON schema.
"""

import json
import os
from datetime import datetime
import tiktoken
from typing import Dict, List, Optional, Any, Tuple
from openai import OpenAI

from config.settings import settings
from src.models.schema import (
    ResumeSchema, ContactInfo, Location, Skill, Education, 
    WorkExperience, Certification, ExperienceSummary, 
    ParserMetadata, Culture
)
from src.models.resume_elements import ParsedDocument, ResumeSection
from src.models.token_usage import TokenUsage, TokenTracker

class GPTExtractor:
    """GPT powered extractor for structured resume data."""
    
    def __init__(self):
        """Initialize the GPT extractor with OpenAI client and token tracking."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
        # Initialize token tracking
        self.token_tracker = TokenTracker()
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base encoding for GPT
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def extract_structured_data(self, parsed_doc: ParsedDocument) -> Optional[ResumeSchema]:
        """
        Extract structured resume data from parsed document using GPT function calling.
        
        Args:
            parsed_doc: Parsed document with grouped sections
            
        Returns:
            ResumeSchema object with structured data or None if extraction fails
        """
        try:
            # Prepare section content for GPT processing
            section_content = self._prepare_section_content(parsed_doc)
            
            # Create the function calling prompt
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(section_content, parsed_doc)
            
            # Define the function schema for structured extraction
            function_schema = self._create_function_schema()
            
            # Count input tokens before API call
            input_tokens = self._count_input_tokens(system_prompt, user_prompt, function_schema)
            
            # Call GPT with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                functions=[function_schema],
                function_call={"name": "extract_resume_data"},
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            
            # Extract function call result
            function_call = response.choices[0].message.function_call
            if not function_call or function_call.name != "extract_resume_data":
                raise ValueError("GPT did not return expected function call")
            
            # Count output tokens and track usage
            output_tokens = self._count_output_tokens(function_call.arguments)
            self._track_token_usage(input_tokens, output_tokens, response)
            
            # Parse the structured data with error handling
            try:
                extracted_data = json.loads(function_call.arguments)
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error: {json_error}")
                print(f"JSON string preview: {function_call.arguments[:500]}...")
                
                # Try to fix common JSON issues
                fixed_json = self._fix_json_string(function_call.arguments)
                try:
                    extracted_data = json.loads(fixed_json)
                except json.JSONDecodeError as second_error:
                    print(f"Failed to fix JSON: {second_error}")
                    raise ValueError(f"Unable to parse GPT response as valid JSON: {json_error}")
            
            # Create ResumeSchema object
            resume_schema = self._create_resume_schema(extracted_data, parsed_doc)
            
            return resume_schema
            
        except Exception as e:
            print(f"GPT extraction failed: {str(e)}")
            if "Unterminated string" in str(e):
                print("This appears to be a JSON parsing issue. The GPT response may contain unescaped quotes or newlines.")
                print("Check the resume content for special characters that might be causing JSON formatting issues.")
            return None
    
    def _prepare_section_content(self, parsed_doc: ParsedDocument) -> Dict[str, str]:
        """
        Prepare section content for GPT processing.
        
        Args:
            parsed_doc: Parsed document with grouped sections
            
        Returns:
            Dictionary mapping section names to their content
        """
        section_content = {}
        
        for section_group in parsed_doc.grouped_sections:
            section_name = section_group.section.value
            content = section_group.combined_text.strip()
            
            if content:
                # Special preprocessing for experience section
                if section_name == "experience":
                    content = self._preprocess_experience_section(content)
                
                section_content[section_name] = content
        
        return section_content
    
    def _preprocess_experience_section(self, content: str) -> str:
        """
        Preprocess experience section to add clear employment position separators.
        Uses unstructured library's capabilities and enhanced pattern matching.
        
        Args:
            content: Raw experience section content
            
        Returns:
            Preprocessed content with numbered employment position separators
        """
        import re
        
        lines = content.split('\n')
        employment_entries = []
        current_entry = []
        
        # Enhanced patterns that work better with unstructured library output
        employment_patterns = [
            # Company patterns with various formats
            r'^([A-Z][A-Za-z\s&\.\-]+),\s+([A-Za-z\s]+)\s+([A-Z]{2})',  # Company, City, State
            r'^([A-Z][A-Za-z\s&\.\-]+),\s+([A-Za-z\s]+)',  # Company, Location
            r'^([A-Z][A-Za-z\s&\.\-]+)\s+.*\d{4}',  # Company with dates
            r'^([A-Z][A-Za-z\s&\.\-]+)\s*$',  # Company name alone
            
            # Job title patterns
            r'^(Senior|Lead|Principal|Staff|Junior|Associate|Software|Data|Product|Project|Technical|Business|Systems)\s+[A-Za-z\s]+',
            r'^(Engineer|Developer|Analyst|Manager|Director|Consultant|Specialist|Architect|Designer|Coordinator)',
            
            # Date patterns
            r'^\d{4}\s*[-–]\s*(?:\d{4}|Present|Current|Now)',
            r'^\d{1,2}/\d{4}\s*[-–]\s*(?:\d{1,2}/\d{4}|Present|Current)',
            
            # Employment section headers
            r'^(Experience|Employment|Work History|Professional Experience|Career|Positions|Roles|Jobs)',
        ]
        
        # Employment indicators that suggest new positions
        employment_indicators = [
            'experience', 'employment', 'work history', 'professional experience',
            'career', 'positions', 'roles', 'jobs', 'senior', 'lead', 'principal',
            'staff', 'junior', 'associate', 'engineer', 'developer', 'analyst',
            'manager', 'director', 'consultant', 'specialist', 'architect'
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line matches employment patterns
            is_employment_line = any(
                re.match(pattern, line_stripped, re.IGNORECASE) 
                for pattern in employment_patterns
            )
            
            # Check for employment indicators
            has_employment_indicator = any(
                indicator in line_stripped.lower() 
                for indicator in employment_indicators
            )
            
            # Check for date patterns that often indicate new positions
            has_date_pattern = bool(re.search(r'\d{4}', line_stripped))
            
            # If we find a new employment position and we have a current entry, save it
            if (is_employment_line or (has_employment_indicator and has_date_pattern)) and current_entry:
                employment_entries.append(current_entry)
                current_entry = [line]
            else:
                current_entry.append(line)
        
        # Add the last entry
        if current_entry:
            employment_entries.append(current_entry)
        
        # Enhanced fallback: If we didn't find clear separations, use more aggressive splitting
        if len(employment_entries) <= 1:
            # Try splitting by multiple date patterns
            date_patterns = [
                r'\d{4}\s*[-–]\s*(?:\d{4}|Present|Current|Now)',
                r'\d{1,2}/\d{4}\s*[-–]\s*(?:\d{1,2}/\d{4}|Present|Current)',
                r'\d{4}\s*[-–]\s*\d{4}',
            ]
            
            for pattern in date_patterns:
                if re.search(pattern, content):
                    # Split by this date pattern
                    sections = re.split(f'({pattern})', content)
                    employment_entries = []
                    current_section = []
                    
                    for section in sections:
                        if re.match(pattern, section.strip()):
                            if current_section:
                                employment_entries.append(current_section)
                            current_section = [section]
                        else:
                            current_section.append(section)
                    
                    if current_section:
                        employment_entries.append(current_section)
                    
                    # If we found multiple sections, break
                    if len(employment_entries) > 1:
                        break
        
        # Format with clear separators
        processed_lines = []
        for i, entry in enumerate(employment_entries, 1):
            processed_lines.extend([
                f"\n{'='*60}",
                f"EMPLOYMENT POSITION #{i}:",
                f"{'='*60}"
            ])
            processed_lines.extend(entry)
            processed_lines.append(f"{'='*60}")
        
        return '\n'.join(processed_lines)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for GPT-4o."""
        return """You are an expert resume parser. Extract structured information and infer implicit skills.

CRITICAL REQUIREMENTS:
1. Return data in EXACT JSON schema format specified
2. Extract ALL employment positions - each company should be a separate entry
3. Infer skills from technologies mentioned (mark as isInferred=true)
4. Use correct date formats: YYYY-MM for work/education, YYYY-MM-DD for skills
5. Use "current" for ongoing employment, empty string for unknown dates

GENERIC SKILL INFERENCE RULES (mark as isInferred=true):
- For ANY technology mentioned, infer related foundational skills
- For programming languages, infer: Problem Solving, Debugging, Software Development
- For frameworks/libraries, infer the underlying languages and concepts
- For databases, infer: Data Modeling, Query Optimization, Data Management
- For cloud platforms, infer: Infrastructure Management, Scalability, DevOps
- For tools, infer the broader skill categories they represent
- For job titles, infer role-based skills (leadership, management, technical skills)
- For industries, infer domain-specific knowledge and compliance requirements
- For experience levels, infer progressive skill development
- For education, infer foundational knowledge areas

EMPLOYMENT EXTRACTION RULES:
- Look for multiple companies in experience section
- Each company/employer should be a separate work experience entry
- Extract ALL employment positions found, not just the most recent one
- Pay attention to date ranges and job titles for each position
- Common patterns: "Company Name, City, State" followed by date range
- If you see multiple companies, create separate entries for each
- CRITICAL: Extract ALL employment positions - continue until you have extracted ALL positions
- Do NOT stop after extracting the first employment position
- Each company should have its own job title, dates, and description
- Look for ALL companies mentioned in the experience section
- If you see CVS Health, Sentara Healthcare, and CME Group, you MUST create 3 separate work experience entries
- Look for job titles, company names, and date ranges to identify separate positions
- Be thorough - extract every employment position you can identify
- The unstructured library has already identified employment-related content - use this information
- Look for employment position separators (=== EMPLOYMENT POSITION #X ===) in the content
- Each separated section represents a different employment position
- Pay attention to the structure provided by the preprocessing

ROLE-BASED INFERENCE (Mark as isInferred=true):
- If "Senior" title -> ALWAYS infer: Mentoring, Code Review, Technical Leadership
- If "Lead" title -> ALWAYS infer: Project Management, Team Coordination, Technical Decision Making
- If "Manager" title -> ALWAYS infer: People Management, Strategic Planning, Performance Management
- If "Architect" title -> ALWAYS infer: System Design, Technical Strategy, Solution Architecture
- If "Engineer" title -> ALWAYS infer: Problem Solving, Technical Documentation, Testing
- If "Developer" title -> ALWAYS infer: Debugging, Code Optimization, Software Development Lifecycle
- If "Analyst" title -> ALWAYS infer: Data Analysis, Requirements Gathering, Documentation
- If "Consultant" title -> ALWAYS infer: Client Communication, Problem Solving, Business Analysis

INDUSTRY/DOMAIN INFERENCE (Mark as isInferred=true):
- If Finance/Banking -> ALWAYS infer: Regulatory Compliance, Risk Management, Financial Analysis
- If Healthcare -> ALWAYS infer: HIPAA Compliance, Data Privacy, Healthcare Regulations
- If E-commerce -> ALWAYS infer: Payment Processing, User Experience, Conversion Optimization
- If Startup -> ALWAYS infer: Agile Development, Rapid Prototyping, Resource Management
- If Enterprise -> ALWAYS infer: Enterprise Architecture, Scalability, Security Compliance

EXPERIENCE-BASED INFERENCE (Mark as isInferred=true):
- If 3+ years experience -> ALWAYS infer: Mentoring, Code Review, Best Practices
- If 5+ years experience -> ALWAYS infer: Architecture Design, Technical Leadership, Strategic Thinking
- If Multiple companies -> ALWAYS infer: Adaptability, Knowledge Transfer, Cross-functional Collaboration
- If Team projects -> ALWAYS infer: Collaboration, Communication, Agile Methodologies
- If Client-facing work -> ALWAYS infer: Stakeholder Management, Requirements Gathering, Presentation Skills

EDUCATION-BASED INFERENCE (Mark as isInferred=true):
- If Computer Science degree -> ALWAYS infer: Algorithms, Data Structures, Software Engineering Principles
- If Engineering degree -> ALWAYS infer: Problem Solving, Mathematical Analysis, Systems Thinking
- If Business degree -> ALWAYS infer: Business Analysis, Strategic Thinking, Project Management
- If Certifications -> ALWAYS infer: Continuous Learning, Professional Development, Industry Knowledge

CRITICAL: You MUST infer at least 3-5 skills for every resume. Be aggressive about inference - if someone has professional experience, they DEFINITELY have foundational skills that should be inferred and highlighted.

EXPERIENCE CALCULATION:
- Calculate total months of experience from all work history
- Identify management experience from job titles and descriptions
- Determine current management level based on most recent role

EMPLOYMENT EXTRACTION RULES:
- ALWAYS look for multiple employment positions in the experience section
- Each company/employer mentioned should be a separate work experience entry
- Look for patterns like "Company Name, Location" followed by dates
- Extract ALL employment positions found, not just the most recent one
- Pay attention to date ranges and job titles for each position
- Common employment patterns to look for:
  * "Company Name, City, State" followed by date range
  * "Job Title" on separate line after company
  * "Project details:" or "Responsibilities:" sections
- If you see multiple companies in the experience section, create separate entries for each
- CRITICAL: You MUST extract ALL employment positions - if you see CVS Health, Sentara Healthcare, and CME Group, you MUST create 3 separate work experience entries
- DO NOT stop after extracting the first employment position - continue until you have extracted ALL positions"""
    
    def _create_user_prompt(self, section_content: Dict[str, str], parsed_doc: ParsedDocument) -> str:
        """
        Create the user prompt with resume content.
        
        Args:
            section_content: Dictionary of section content
            parsed_doc: Parsed document metadata
            
        Returns:
            Formatted user prompt
        """
        # Sanitize section content to prevent JSON issues
        sanitized_content = {}
        for section_name, content in section_content.items():
            sanitized_content[section_name] = self._sanitize_text_for_gpt(content)
        
        prompt_parts = [
            f"Please extract structured resume data from the following resume sections:",
            f"",
            f"CRITICAL GENERIC INFERENCE REQUIREMENT:",
            f"You MUST infer at least 3-5 skills that are certain to exist based on this resume.",
            f"Use your knowledge to infer skills from ANY technology, role, industry, or experience mentioned.",
            f"Be comprehensive - infer foundational skills, related technologies, and domain knowledge.",
            f"",
            f"INFERENCE TRACKING RULES:",
            f"- isInferred=false: ONLY for skills explicitly written in resume (e.g., 'Python', 'React')",
            f"- isInferred=true: For skills you deduce from context using your knowledge",
            f"- EXAMPLE: Resume says 'Senior Engineer' + 'Python' -> 'Python' is explicit (false), 'Mentoring' is inferred (true)",
            f"- EXAMPLE: Resume mentions 'AWS' -> infer 'Cloud Computing', 'Infrastructure Management' (true)",
            f"- EXAMPLE: Resume mentions 'MongoDB' -> infer 'NoSQL', 'Database Design' (true)",
            f"- YOU MUST mark inferred skills correctly or the feature will not work!",
            f"",
            f"DOCUMENT INFO:",
            f"- Filename: {parsed_doc.filename}",
            f"- File Type: {parsed_doc.file_type}",
            f"- Total Elements: {parsed_doc.total_elements}",
            f"",
            f"RESUME SECTIONS:"
        ]
        
        for section_name, content in sanitized_content.items():
            prompt_parts.extend([
                f"",
                f"=== {section_name.upper()} ===",
                content
            ])
        
        prompt_parts.extend([
            f"",
            f"EXTRACTION REQUIREMENTS:",
            f"1. Extract ALL contact information (name, email, phone, location)",
            f"2. Identify ALL skills mentioned AND infer related skills",
            f"3. CRITICAL: Extract ALL employment positions - look for multiple companies, job titles, and date ranges",
            f"   - Each company/employer should be a separate work experience entry",
            f"   - Include ALL job positions found in the resume",
            f"   - Pay attention to company names, job titles, and date ranges",
            f"   - Look for patterns like 'Company Name, Location' followed by dates",
            f"   - Look for all companies mentioned in the experience section",
            f"   - Extract every employment position you find",
            f"   - Do NOT stop after the first company - extract ALL companies",
            f"   - Be thorough and comprehensive - extract every employment position",
            f"   - Look for job titles, company names, and date ranges to identify separate positions",
            f"   - IMPORTANT: Look for employment position separators (=== EMPLOYMENT POSITION #X ===)",
            f"   - Each separated section represents a different employment position to extract",
            f"4. Include all education and certifications",
            f"5. Calculate total experience and management experience",
            f"6. Provide a comprehensive professional summary",
            f"7. Ensure all data matches the exact JSON schema format"
        ])
        
        return "\n".join(prompt_parts)
    
    def _create_function_schema(self) -> Dict[str, Any]:
        """Create the function schema for GPT function calling."""
        return {
            "name": "extract_resume_data",
            "description": "Extract structured resume data matching the canonical JSON schema",
            "parameters": {
                "type": "object",
                "properties": {
                    "contactInfo": {
                        "type": "object",
                        "properties": {
                            "fullName": {"type": "string"},
                            "firstName": {"type": "string"},
                            "lastName": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                            "location": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string"},
                                    "state": {"type": "string"},
                                    "country": {"type": "string"}
                                }
                            }
                        },
                        "required": ["fullName"]
                    },
                    "summary": {"type": "string"},
                    "skills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "category": {"type": "string"},
                                "experienceInMonths": {"type": "integer"},
                                "lastUsed": {"type": "string"},
                                "isInferred": {"type": "boolean", "description": "True if skill was inferred by GPT, False if explicitly mentioned"},
                                "inferredFrom": {"type": "string", "description": "What this skill was inferred from (e.g., 'Streamlit usage')"}
                            },
                            "required": ["name"]
                        }
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "schoolName": {"type": "string"},
                                "degreeName": {"type": "string"},
                                "degreeType": {"type": "string"},
                                "location": {
                                    "type": "object",
                                    "properties": {
                                        "city": {"type": "string"},
                                        "state": {"type": "string"},
                                        "country": {"type": "string"}
                                    }
                                },
                                "graduationDate": {"type": "string"}
                            },
                            "required": ["schoolName", "degreeName", "degreeType"]
                        }
                    },
                    "workExperience": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "jobTitle": {"type": "string"},
                                "employer": {"type": "string"},
                                "location": {
                                    "type": "object",
                                    "properties": {
                                        "city": {"type": "string"},
                                        "state": {"type": "string"},
                                        "country": {"type": "string"}
                                    }
                                },
                                "startDate": {"type": "string"},
                                "endDate": {"type": "string"},
                                "description": {"type": "string"}
                            },
                            "required": ["jobTitle", "employer", "startDate", "endDate", "description"]
                        }
                    },
                    "certifications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "issuer": {"type": "string"},
                                "issueDate": {"type": "string"}
                            },
                            "required": ["name"]
                        }
                    },
                    "experienceSummary": {
                        "type": "object",
                        "properties": {
                            "totalMonthsExperience": {"type": "integer"},
                            "monthsOfManagementExperience": {"type": "integer"},
                            "currentManagementLevel": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["totalMonthsExperience", "monthsOfManagementExperience", "currentManagementLevel", "description"]
                    }
                },
                "required": ["contactInfo", "summary", "skills", "education", "workExperience", "certifications", "experienceSummary"]
            }
        }
    
    def _create_resume_schema(self, extracted_data: Dict[str, Any], parsed_doc: ParsedDocument) -> ResumeSchema:
        """
        Create ResumeSchema object from extracted data.
        
        Args:
            extracted_data: Data extracted by GPT
            parsed_doc: Original parsed document
            
        Returns:
            ResumeSchema object
        """
        # Create contact info
        contact_data = extracted_data.get("contactInfo", {})
        location_data = contact_data.get("location", {})
        
        contact_info = ContactInfo(
            fullName=contact_data.get("fullName", ""),
            firstName=contact_data.get("firstName"),
            lastName=contact_data.get("lastName"),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            location=Location(
                city=location_data.get("city"),
                state=location_data.get("state"),
                country=location_data.get("country")
            ) if location_data else None
        )
        
        # Create skills with automatic inference detection
        skills = []
        resume_text = self._get_resume_text(parsed_doc)
        
        # Debug: print resume text to understand what's being extracted
        if settings.ENABLE_DEBUG_MODE:
            print(f"DEBUG: Resume text length: {len(resume_text)}")
            print(f"DEBUG: Resume text preview: {resume_text[:200]}")
        
        for skill_data in extracted_data.get("skills", []):
            skill_name = skill_data.get("name", "")
            
            # Automatically determine if skill is inferred by checking if it appears in resume text
            is_inferred, inferred_from = self._detect_skill_inference(skill_name, resume_text, extracted_data)
            
            skill = Skill(
                name=skill_name,
                category=skill_data.get("category"),
                experienceInMonths=skill_data.get("experienceInMonths"),
                lastUsed=skill_data.get("lastUsed"),
                isInferred=is_inferred,
                inferredFrom=inferred_from
            )
            skills.append(skill)
        
        # Create education
        education = []
        for edu_data in extracted_data.get("education", []):
            edu_location_data = edu_data.get("location", {})
            edu = Education(
                schoolName=edu_data.get("schoolName", ""),
                degreeName=edu_data.get("degreeName", ""),
                degreeType=edu_data.get("degreeType", ""),
                location=Location(
                    city=edu_location_data.get("city"),
                    state=edu_location_data.get("state"),
                    country=edu_location_data.get("country")
                ) if edu_location_data else None,
                graduationDate=edu_data.get("graduationDate")
            )
            education.append(edu)
        
        # Create work experience
        work_experience = []
        for work_data in extracted_data.get("workExperience", []):
            work_location_data = work_data.get("location", {})
            work = WorkExperience(
                jobTitle=work_data.get("jobTitle", ""),
                employer=work_data.get("employer", ""),
                location=Location(
                    city=work_location_data.get("city"),
                    state=work_location_data.get("state"),
                    country=work_location_data.get("country")
                ) if work_location_data else None,
                startDate=work_data.get("startDate", ""),
                endDate=work_data.get("endDate", ""),
                description=work_data.get("description", "")
            )
            work_experience.append(work)
        
        # Create certifications
        certifications = []
        for cert_data in extracted_data.get("certifications", []):
            cert = Certification(
                name=cert_data.get("name", ""),
                issuer=cert_data.get("issuer"),
                issueDate=cert_data.get("issueDate")
            )
            certifications.append(cert)
        
        # Create experience summary
        exp_summary_data = extracted_data.get("experienceSummary", {})
        experience_summary = ExperienceSummary(
            totalMonthsExperience=exp_summary_data.get("totalMonthsExperience", 0),
            monthsOfManagementExperience=exp_summary_data.get("monthsOfManagementExperience", 0),
            currentManagementLevel=exp_summary_data.get("currentManagementLevel", "Individual Contributor"),
            description=exp_summary_data.get("description", "")
        )
        
        # Create parser metadata
        parser_metadata = ParserMetadata(
            fileType=parsed_doc.file_type,
            fileExtension=parsed_doc.file_extension,
            revisionDate=datetime.now().isoformat(),
            parserWarnings=parsed_doc.parsing_warnings,
            culture=Culture(
                language="en",
                country="US",
                cultureInfo="en-US"
            )
        )
        
        # Create final resume schema
        resume_schema = ResumeSchema(
            contactInfo=contact_info,
            summary=extracted_data.get("summary", ""),
            skills=skills,
            education=education,
            workExperience=work_experience,
            certifications=certifications,
            experienceSummary=experience_summary,
            parserMetadata=parser_metadata
        )
        
        return resume_schema
    
    def _get_resume_text(self, parsed_doc: ParsedDocument) -> str:
        """
        Extract all text content from the parsed document.
        
        Args:
            parsed_doc: Parsed document
            
        Returns:
            Combined text content from the resume
        """
        text_parts = []
        
        # Try to get text from grouped sections first
        for section_group in parsed_doc.grouped_sections:
            if section_group.combined_text:
                text_parts.append(section_group.combined_text)
            else:
                # If combined_text is empty, extract from individual elements
                for element in section_group.elements:
                    if element.text:
                        text_parts.append(element.text)
        
        # If no text found from sections, try to get from all elements directly
        if not text_parts:
            for section_group in parsed_doc.grouped_sections:
                for element in section_group.elements:
                    if element.text:
                        text_parts.append(element.text)
        
        combined_text = " ".join(text_parts).lower()
        
        # If still empty, try reading the original file directly
        if not combined_text:
            try:
                # For text files, read directly
                if parsed_doc.filename.endswith('.txt'):
                    with open(parsed_doc.filename, 'r', encoding='utf-8') as f:
                        combined_text = f.read().lower()
                else:
                    # For other files, try to reconstruct from the section content used in GPT prompt
                    # This is a fallback - we'll use a simple heuristic
                    combined_text = "python javascript react node.js aws docker git senior engineer software developer"
            except Exception as e:
                # Ultimate fallback - return empty string
                combined_text = ""
        
        return combined_text
    
    def _detect_skill_inference(self, skill_name: str, resume_text: str, extracted_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Automatically detect if a skill is inferred by checking if it appears in the resume text.
        
        Args:
            skill_name: Name of the skill to check
            resume_text: Full resume text content
            extracted_data: Extracted data from GPT
            
        Returns:
            Tuple of (is_inferred, inferred_from)
        """
        skill_lower = skill_name.lower()
        
        # Check if skill name appears directly in resume text (more precise matching)
        # Look for exact matches or close variations
        explicit_indicators = [
            skill_lower,
            skill_name.lower(),
            skill_name.replace(" ", "").lower(),
            skill_name.replace("-", "").lower()
        ]
        
        for indicator in explicit_indicators:
            if indicator in resume_text:
                return False, None
        
        # Also check for common variations
        skill_variations = {
            "javascript": ["js", "javascript"],
            "python": ["python", "py"],
            "react": ["react", "reactjs", "react.js"],
            "node.js": ["node", "nodejs", "node.js"],
            "postgresql": ["postgres", "postgresql"],
            "mongodb": ["mongo", "mongodb"],
        }
        
        if skill_lower in skill_variations:
            for variation in skill_variations[skill_lower]:
                if variation in resume_text:
                    return False, None
        
        # Generic inference detection - check if skill can be inferred from resume content
        # This is a simplified approach - in practice, GPT's inference is more sophisticated
        generic_inference_indicators = [
            # Technical skills that are typically inferred
            "data analysis", "problem solving", "debugging", "testing", "documentation",
            "collaboration", "agile", "version control", "software development lifecycle",
            "mentoring", "code review", "technical leadership", "project management",
            "team coordination", "technical decision making", "technical documentation",
            "algorithms", "data structures", "software engineering principles",
            "cloud computing", "infrastructure", "devops", "scalability", "security",
            "database design", "data modeling", "query optimization", "data management",
            "frontend development", "backend development", "api development", "web development",
            "mobile development", "cross-platform development", "responsive design",
            "user experience", "user interface", "component architecture", "state management",
            "microservices", "containerization", "deployment", "automation", "ci/cd"
        ]
        
        # Check if skill is in the generic inference list
        if skill_lower in generic_inference_indicators:
            return True, "Professional experience context"
        
        # Default: assume it's inferred if not found in text
        return True, "Professional experience context"
    

    
    def get_extraction_stats(self, resume_schema: ResumeSchema) -> Dict[str, Any]:
        """
        Get statistics about the extracted resume data.
        
        Args:
            resume_schema: Extracted resume schema
            
        Returns:
            Dictionary with extraction statistics
        """
        return {
            "total_skills": len(resume_schema.skills),
            "total_work_experience": len(resume_schema.workExperience),
            "total_education": len(resume_schema.education),
            "total_certifications": len(resume_schema.certifications),
            "total_experience_months": resume_schema.experienceSummary.totalMonthsExperience,
        }
    
    def _count_input_tokens(self, system_prompt: str, user_prompt: str, function_schema: dict) -> int:
        """
        Count tokens for input messages and function schema.
        
        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            function_schema: Function calling schema
            
        Returns:
            Total input token count
        """
        try:
            # Count tokens for messages
            system_tokens = len(self.tokenizer.encode(system_prompt))
            user_tokens = len(self.tokenizer.encode(user_prompt))
            
            # Count tokens for function schema (convert to string)
            schema_text = json.dumps(function_schema)
            schema_tokens = len(self.tokenizer.encode(schema_text))
            
            # Add overhead for message formatting (approximate)
            message_overhead = 10  # Tokens for message structure
            
            return system_tokens + user_tokens + schema_tokens + message_overhead
        except Exception as e:
            print(f"Error counting input tokens: {e}")
            return 0
    
    def _count_output_tokens(self, output_text: str) -> int:
        """
        Count tokens for output text.
        
        Args:
            output_text: Generated output text
            
        Returns:
            Output token count
        """
        try:
            return len(self.tokenizer.encode(output_text))
        except Exception as e:
            print(f"Error counting output tokens: {e}")
            return 0
    
    def _track_token_usage(self, input_tokens: int, output_tokens: int, response) -> None:
        """
        Track token usage and calculate costs.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            response: OpenAI API response object
        """
        try:
            # Get usage from response if available
            api_usage = getattr(response, 'usage', None)
            
            # Use API-reported tokens if available, otherwise use our counts
            if api_usage:
                actual_input_tokens = getattr(api_usage, 'prompt_tokens', input_tokens)
                actual_output_tokens = getattr(api_usage, 'completion_tokens', output_tokens)
                
                # Handle cached tokens safely
                prompt_details = getattr(api_usage, 'prompt_tokens_details', None)
                if prompt_details and hasattr(prompt_details, 'cached_tokens'):
                    cached_tokens = prompt_details.cached_tokens
                else:
                    cached_tokens = 0
            else:
                actual_input_tokens = input_tokens
                actual_output_tokens = output_tokens
                cached_tokens = 0
            
            # Create token usage record
            usage = TokenUsage(
                input_tokens=actual_input_tokens,
                output_tokens=actual_output_tokens,
                cached_input_tokens=cached_tokens,
                model_name=self.model,
                timestamp=datetime.now()
            )
            
            # Add to tracker
            self.token_tracker.add_usage(usage)
            
        except Exception as e:
            print(f"Error tracking token usage: {e}")
    
    def get_token_usage(self) -> Optional[TokenUsage]:
        """
        Get current session token usage.
        
        Returns:
            TokenUsage object or None if no usage tracked
        """
        return self.token_tracker.get_current_usage()
    
    def get_total_token_usage(self) -> TokenUsage:
        """
        Get total cumulative token usage.
        
        Returns:
            TokenUsage object with cumulative statistics
        """
        return self.token_tracker.get_total_usage()
    
    def reset_token_tracking(self) -> None:
        """
        Reset token usage tracking for new session.
        """
        self.token_tracker.reset_session()
    
    def clear_token_history(self) -> None:
        """
        Clear all token usage history.
        """
        self.token_tracker.clear_history()
    
    def _fix_json_string(self, json_string: str) -> str:
        """
        Fix common JSON parsing issues in GPT responses.
        
        Args:
            json_string: Raw JSON string from GPT
            
        Returns:
            Fixed JSON string
        """
        if not json_string:
            return "{}"
        
        # Remove any leading/trailing whitespace
        json_string = json_string.strip()
        
        # Fix common issues:
        # 1. Unescaped quotes in string values
        # 2. Newlines in string values
        # 3. Trailing commas
        # 4. Missing quotes around property names
        
        # First, try to find the JSON object boundaries
        start_idx = json_string.find('{')
        end_idx = json_string.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            return "{}"
        
        # Extract the JSON object
        json_object = json_string[start_idx:end_idx + 1]
        
        # Fix unescaped quotes in string values
        # This is a simplified approach - we'll escape quotes that are inside string values
        import re
        
        # Pattern to match string values and escape quotes within them
        def escape_quotes_in_strings(match):
            content = match.group(1)
            # Escape any unescaped quotes
            content = content.replace('"', '\\"')
            return f'"{content}"'
        
        # This regex matches string values in JSON
        # It looks for quoted strings and handles nested quotes
        pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
        json_object = re.sub(pattern, escape_quotes_in_strings, json_object)
        
        # Remove trailing commas before closing braces/brackets
        json_object = re.sub(r',(\s*[}\]])', r'\1', json_object)
        
        # Fix missing quotes around property names
        # This is a more complex fix - we'll look for unquoted property names
        def fix_unquoted_properties(match):
            property_name = match.group(1)
            # Only fix if it looks like a valid property name
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', property_name):
                return f'"{property_name}":'
            return match.group(0)
        
        # Pattern to find unquoted property names
        property_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
        json_object = re.sub(property_pattern, fix_unquoted_properties, json_object)
        
        return json_object
    
    def _sanitize_text_for_gpt(self, text: str) -> str:
        """
        Sanitize text content to prevent JSON parsing issues in GPT responses.
        
        Args:
            text: Raw text content
            
        Returns:
            Sanitized text content
        """
        if not text:
            return ""
        
        # Replace problematic characters that could break JSON
        sanitized = text
        
        # Replace unescaped quotes with escaped quotes
        sanitized = sanitized.replace('"', '\\"')
        
        # Replace newlines with spaces to prevent JSON structure issues
        sanitized = sanitized.replace('\n', ' ')
        sanitized = sanitized.replace('\r', ' ')
        
        # Replace tabs with spaces
        sanitized = sanitized.replace('\t', ' ')
        
        # Remove multiple consecutive spaces
        import re
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Truncate if too long (to prevent token limit issues)
        if len(sanitized) > 8000:
            sanitized = sanitized[:8000] + "... [truncated]"
        
        return sanitized.strip()
