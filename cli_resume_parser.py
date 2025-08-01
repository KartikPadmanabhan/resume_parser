#!/usr/bin/env python3
"""
Command-line equivalent of the Streamlit resume parser app.
Provides all the same functionality without requiring a browser interface.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import traceback
from datetime import datetime
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from src.ui.file_validator import FileValidator, FileValidationError
from src.models.schema import ResumeSchema
from src.parsers.document_parser import DocumentParser
from src.parsers.content_processor import ContentProcessor
from src.models.resume_elements import ParsedDocument
from src.agents.gpt_extractor import GPTExtractor

class CLIResumeParser:
    """Command-line resume parser that replicates Streamlit app functionality."""
    
    def __init__(self):
        """Initialize the CLI parser with all components."""
        self.validator = FileValidator()
        self.document_parser = DocumentParser()
        self.content_processor = ContentProcessor()
        self.gpt_extractor = None  # Initialize lazily to handle API key issues
        
        # Results storage
        self.parsed_document = None
        self.structured_resume = None
        
    def print_header(self):
        """Print application header."""
        print("=" * 80)
        print("🔍 AI-POWERED RESUME PARSER - COMMAND LINE INTERFACE")
        print("=" * 80)
        print("📄 Upload a resume to extract structured information using AI")
        print()
        
    def print_separator(self, title: str = ""):
        """Print a section separator."""
        if title:
            print(f"\n{'─' * 20} {title} {'─' * (57 - len(title))}")
        else:
            print("─" * 80)
    
    def validate_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Validate and prepare file for processing.
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary with file info if valid, None otherwise
        """
        self.print_separator("FILE VALIDATION")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        except Exception as e:
            print(f"❌ Failed to read file: {str(e)}")
            return None
        
        filename = Path(file_path).name
        file_size_mb = len(file_content) / (1024 * 1024)
        
        # Get file info
        file_info = {
            "filename": filename,
            "size_bytes": len(file_content),
            "size_mb": round(file_size_mb, 2),
            "file_type": Path(file_path).suffix.upper().replace('.', '') + " Document"
        }
        
        print(f"📁 File Name: {file_info['filename']}")
        print(f"📊 File Type: {file_info['file_type']}")
        print(f"📏 File Size: {file_info['size_mb']} MB")
        
        # Validate file
        try:
            is_valid, errors = self.validator.validate_uploaded_file(
                file_content, filename, None
            )
            
            if not is_valid:
                print("❌ File validation failed:")
                for error in errors:
                    print(f"  • {error}")
                return None
            
            print("✅ File validation passed!")
            
            return {
                "content": file_content,
                "filename": filename,
                "file_info": file_info,
                "file_path": file_path
            }
            
        except Exception as e:
            print(f"❌ File validation error: {str(e)}")
            return None
    
    def process_document(self, file_data: Dict[str, Any]) -> Optional[ParsedDocument]:
        """
        Process uploaded document using unstructured library.
        
        Args:
            file_data: Dictionary containing file content and metadata
            
        Returns:
            ParsedDocument with extracted elements or None if failed
        """
        self.print_separator("DOCUMENT PROCESSING")
        
        try:
            print("🔄 Processing document...")
            print("📄 Step 1/2: Extracting document elements...")
            
            # Parse document with unstructured
            parsed_doc = self.document_parser.parse_document(
                file_content=file_data["content"],
                filename=file_data["filename"],
                mime_type=file_data.get("mime_type")
            )
            
            if parsed_doc.parsing_warnings:
                for warning in parsed_doc.parsing_warnings:
                    print(f"⚠️  {warning}")
            
            print("🗂️  Step 2/2: Grouping content by sections...")
            
            # Get the extracted elements from the parsed document
            elements = getattr(parsed_doc, '_raw_elements', [])
            
            processed_doc = self.content_processor.process_document(parsed_doc, elements)
            
            print("✅ Document processing complete!")
            
            # Show processing results
            print(f"📊 Total elements extracted: {processed_doc.total_elements}")
            print(f"📂 Sections identified: {len(processed_doc.grouped_sections)}")
            
            if processed_doc.grouped_sections:
                section_names = [group.section.value for group in processed_doc.grouped_sections]
                print(f"📋 Sections found: {', '.join(section_names)}")
            
            return processed_doc
            
        except Exception as e:
            print(f"❌ Document processing failed: {str(e)}")
            if settings.ENABLE_DEBUG_MODE:
                print("🐛 Debug traceback:")
                print(traceback.format_exc())
            return None
    
    def _initialize_gpt_extractor(self) -> bool:
        """
        Initialize GPT extractor with proper error handling.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self.gpt_extractor is not None:
            return True
        
        try:
            self.gpt_extractor = GPTExtractor()
            return True
        except ValueError as e:
            print(f"❌ OpenAI API configuration error: {str(e)}")
            print("💡 Please set your OPENAI_API_KEY in the .env file")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize GPT extractor: {str(e)}")
            return False
    
    def extract_structured_data(self, parsed_doc: ParsedDocument) -> Optional[ResumeSchema]:
        """
        Extract structured resume data using GPT-4o.
        
        Args:
            parsed_doc: Parsed document with grouped sections
            
        Returns:
            ResumeSchema with structured data or None if extraction fails
        """
        self.print_separator("GPT-4O EXTRACTION")
        
        try:
            print("🤖 Extracting structured data with GPT-4o...")
            print("🔧 Step 1/3: Initializing AI extractor...")
            
            if not self._initialize_gpt_extractor():
                return None
            
            print("🧠 Step 2/3: Analyzing resume content with GPT-4o...")
            
            structured_data = self.gpt_extractor.extract_structured_data(parsed_doc)
            
            if structured_data:
                print("✅ Step 3/3: Structured data extraction complete!")
                
                # Show extraction statistics
                stats = self.gpt_extractor.get_extraction_stats(structured_data)
                
                print(f"📊 Extraction Statistics:")
                print(f"  🎯 Skills Found: {stats['total_skills']}")
                print(f"  💼 Work Experience: {stats['total_work_experience']}")
                print(f"  🎓 Education: {stats['total_education']}")
                print(f"  ⏱️  Total Experience: {stats['total_experience_months']} months")
                
                # Show token usage and cost information
                self._render_token_usage_stats()
                
                return structured_data
            else:
                print("❌ Structured data extraction failed")
                print("Failed to extract structured data from resume")
                return None
                
        except Exception as e:
            print(f"❌ Structured data extraction failed: {str(e)}")
            if settings.ENABLE_DEBUG_MODE:
                print("🐛 Debug traceback:")
                print(traceback.format_exc())
            return None
    
    def _render_token_usage_stats(self) -> None:
        """
        Render comprehensive token usage and cost statistics.
        """
        if not self.gpt_extractor:
            return
        
        # Get current session token usage
        current_usage = self.gpt_extractor.get_token_usage()
        total_usage = self.gpt_extractor.get_total_token_usage()
        
        if current_usage:
            print("\n💰 GPT-4o Token Usage & Cost Analysis")
            print("─" * 50)
            
            # Current session stats
            print("📊 Current Extraction:")
            print(f"  📥 Input Tokens: {current_usage.input_tokens:,}")
            print(f"     💵 Cost: {current_usage.format_cost(current_usage.input_cost)}")
            
            if current_usage.cached_input_tokens > 0:
                print(f"  💾 Cached Tokens: {current_usage.cached_input_tokens:,}")
                print(f"     💵 Cost: {current_usage.format_cost(current_usage.cached_input_cost)} (50% savings)")
            else:
                print(f"  💾 Cached Tokens: 0")
                print(f"     💵 Cost: $0.000000")
            
            print(f"  📤 Output Tokens: {current_usage.output_tokens:,}")
            print(f"     💵 Cost: {current_usage.format_cost(current_usage.output_cost)}")
            
            print(f"  💰 Total Cost: {current_usage.format_cost(current_usage.total_cost)}")
            
            # Total session stats if available
            if total_usage and total_usage != current_usage:
                print(f"\n📈 Session Totals:")
                print(f"  📥 Total Input: {total_usage.input_tokens:,}")
                print(f"  📤 Total Output: {total_usage.output_tokens:,}")
                print(f"  💰 Session Cost: {total_usage.format_cost(total_usage.total_cost)}")
    
    def render_results(self, structured_resume: Optional[ResumeSchema] = None):
        """
        Render final parsing results in structured format.
        
        Args:
            structured_resume: Parsed resume data to display
        """
        self.print_separator("STRUCTURED RESUME OUTPUT")
        
        if not structured_resume:
            print("ℹ️  No structured data available yet.")
            print("   Run with --extract flag to generate structured resume data")
            return
        
        # Render structured view
        self._render_structured_view(structured_resume)
        
        # Render JSON output
        print("\n" + "─" * 40 + " JSON OUTPUT " + "─" * 40)
        self._render_json_output(structured_resume)
        
        # Render metadata
        self._render_metadata(structured_resume)
    
    def _render_structured_view(self, resume: ResumeSchema):
        """Render structured view of parsed resume."""
        print("📋 STRUCTURED VIEW")
        print("─" * 30)
        
        # Contact Information
        if resume.contactInfo:
            print("👤 CONTACT INFORMATION")
            contact = resume.contactInfo
            if contact.fullName:
                print(f"  📛 Name: {contact.fullName}")
            if contact.email:
                print(f"  📧 Email: {contact.email}")
            if contact.phone:
                print(f"  📞 Phone: {contact.phone}")
            if contact.location:
                location_str = ""
                if contact.location.city:
                    location_str += contact.location.city
                if contact.location.state:
                    location_str += f", {contact.location.state}"
                if contact.location.country:
                    location_str += f", {contact.location.country}"
                if location_str:
                    print(f"  📍 Location: {location_str}")
            print()
        
        # Summary
        if resume.summary:
            print("📝 SUMMARY")
            print(f"  {resume.summary}")
            print()
        
        # Skills
        if resume.skills:
            print(f"🎯 SKILLS ({len(resume.skills)} total)")
            self._render_skills_with_inference(resume.skills)
            print()
        
        # Work Experience
        if resume.workExperience:
            print(f"💼 WORK EXPERIENCE ({len(resume.workExperience)} positions)")
            for i, exp in enumerate(resume.workExperience, 1):
                print(f"  {i}. {exp.jobTitle} at {exp.employer}")
                if exp.startDate or exp.endDate:
                    start = exp.startDate or "Unknown"
                    end = exp.endDate or "Present"
                    print(f"     📅 {start} - {end}")
                if exp.location:
                    location_str = ""
                    if exp.location.city:
                        location_str += exp.location.city
                    if exp.location.state:
                        location_str += f", {exp.location.state}"
                    if exp.location.country:
                        location_str += f", {exp.location.country}"
                    if location_str:
                        print(f"     📍 {location_str}")
                if exp.description:
                    print(f"     📋 Description: {exp.description[:100]}...")
            print()
        
        # Education
        if resume.education:
            print(f"🎓 EDUCATION ({len(resume.education)} entries)")
            for i, edu in enumerate(resume.education, 1):
                print(f"  {i}. {edu.degreeName} ({edu.degreeType})")
                print(f"     🏫 {edu.schoolName}")
                if edu.graduationDate:
                    print(f"     📅 Graduated: {edu.graduationDate}")
                if edu.location:
                    location_str = ""
                    if edu.location.city:
                        location_str += edu.location.city
                    if edu.location.state:
                        location_str += f", {edu.location.state}"
                    if edu.location.country:
                        location_str += f", {edu.location.country}"
                    if location_str:
                        print(f"     📍 {location_str}")
            print()
        
        # Certifications
        if resume.certifications:
            print(f"🏆 CERTIFICATIONS ({len(resume.certifications)} certifications)")
            for i, cert in enumerate(resume.certifications, 1):
                print(f"  {i}. {cert.name}")
                if cert.issuer:
                    print(f"     🏢 Issued by: {cert.issuer}")
                if cert.issueDate:
                    print(f"     📅 Issued: {cert.issueDate}")
            print()
    
    def _render_skills_with_inference(self, skills: List):
        """
        Render skills with color-coded visualization to highlight inferred vs. explicit skills.
        
        Args:
            skills: List of Skill objects from the resume schema
        """
        explicit_skills = []
        inferred_skills = []
        
        for skill in skills:
            if hasattr(skill, 'is_inferred') and skill.is_inferred:
                inferred_skills.append(skill.name)
            else:
                explicit_skills.append(skill.name)
        
        if explicit_skills:
            print(f"  ✅ Explicit Skills ({len(explicit_skills)}): {', '.join(explicit_skills)}")
        
        if inferred_skills:
            print(f"  🔍 Inferred Skills ({len(inferred_skills)}): {', '.join(inferred_skills)}")
    
    def _render_json_output(self, resume: ResumeSchema):
        """Render JSON output view."""
        try:
            json_output = resume.dict()
            print(json.dumps(json_output, indent=2, default=str))
        except Exception as e:
            print(f"❌ Failed to render JSON: {str(e)}")
    
    def _render_metadata(self, resume: ResumeSchema):
        """Render metadata and warnings."""
        print("\n" + "─" * 40 + " METADATA " + "─" * 40)
        
        if hasattr(resume, 'metadata') and resume.metadata:
            metadata = resume.metadata
            print("📊 PARSING METADATA")
            if hasattr(metadata, 'total_sections_found'):
                print(f"  📂 Sections Found: {metadata.total_sections_found}")
            if hasattr(metadata, 'confidence_score'):
                print(f"  🎯 Confidence Score: {metadata.confidence_score}")
            if hasattr(metadata, 'processing_time'):
                print(f"  ⏱️  Processing Time: {metadata.processing_time}s")
        
        # Show any parsing warnings
        if self.parsed_document and self.parsed_document.parsing_warnings:
            print("\n⚠️  PARSING WARNINGS")
            for warning in self.parsed_document.parsing_warnings:
                print(f"  • {warning}")
    
    def save_results(self, output_file: str = None):
        """Save results to JSON file."""
        if not self.structured_resume:
            print("❌ No structured data to save")
            return
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"parsed_resume_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.structured_resume.dict(), f, indent=2, default=str)
            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")
    
    def run_interactive(self, file_path: str, extract: bool = True, save: bool = False, output_file: str = None):
        """
        Run the complete parsing pipeline interactively.
        
        Args:
            file_path: Path to the resume file
            extract: Whether to run GPT extraction
            save: Whether to save results to file
            output_file: Output file path (optional)
        """
        try:
            self.print_header()
            
            # Step 1: File validation
            file_data = self.validate_file(file_path)
            if not file_data:
                return
            
            # Step 2: Document processing
            self.parsed_document = self.process_document(file_data)
            if not self.parsed_document:
                return
            
            # Step 3: GPT extraction (optional)
            if extract:
                self.structured_resume = self.extract_structured_data(self.parsed_document)
            
            # Step 4: Display results
            self.render_results(self.structured_resume)
            
            # Step 5: Save results (optional)
            if save and self.structured_resume:
                self.save_results(output_file)
            
            print("\n" + "=" * 80)
            print("✅ PARSING COMPLETE")
            print("=" * 80)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user")
        except Exception as e:
            print(f"\n❌ Application error: {str(e)}")
            if settings.ENABLE_DEBUG_MODE:
                print("🐛 Debug traceback:")
                print(traceback.format_exc())

def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="AI-Powered Resume Parser - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_resume_parser.py resume.pdf
  python cli_resume_parser.py resume.docx --no-extract
  python cli_resume_parser.py resume.pdf --save --output results.json
  python cli_resume_parser.py tests/sample_resumes/8104692.pdf --save
        """
    )
    
    parser.add_argument(
        'file_path',
        help='Path to the resume file (PDF, DOCX, DOC, TXT, HTML)'
    )
    
    parser.add_argument(
        '--no-extract',
        action='store_true',
        help='Skip GPT extraction (only process document structure)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path (default: auto-generated with timestamp)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed error messages'
    )
    
    args = parser.parse_args()
    
    # Set debug mode if requested
    if args.debug:
        os.environ['ENABLE_DEBUG_MODE'] = 'true'
    
    # Create and run parser
    cli_parser = CLIResumeParser()
    cli_parser.run_interactive(
        file_path=args.file_path,
        extract=not args.no_extract,
        save=args.save,
        output_file=args.output
    )

if __name__ == "__main__":
    main()
