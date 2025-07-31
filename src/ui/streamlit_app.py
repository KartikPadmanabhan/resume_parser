"""
Streamlit frontend application for the intelligent resume parser.
Provides file upload interface and displays parsed results.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any, List
from io import BytesIO
import traceback

from config.settings import settings
from src.ui.file_validator import FileValidator, FileValidationError
from src.models.schema import ResumeSchema
from src.parsers.document_parser import DocumentParser
from src.parsers.content_processor import ContentProcessor
from src.models.resume_elements import ParsedDocument
from src.agents.gpt_extractor import GPTExtractor


class ResumeParserUI:
    """Main Streamlit UI class for resume parsing."""
    
    def __init__(self):
        """Initialize the UI with configuration."""
        self.validator = FileValidator()
        self.document_parser = DocumentParser()
        self.content_processor = ContentProcessor()
        self.gpt_extractor = None  # Initialize lazily to handle API key issues
        self._setup_page_config()
    
    def _setup_page_config(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=settings.APP_TITLE,
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_header(self) -> None:
        """Render the application header."""
        st.title(settings.APP_TITLE)
        st.markdown(f"*{settings.APP_DESCRIPTION}*")
        st.divider()
    
    def render_sidebar(self) -> None:
        """Render the sidebar with settings and information."""
        with st.sidebar:
            st.header("📋 Settings")
            
            # File upload settings
            st.subheader("File Upload")
            st.write(f"**Max file size:** {settings.MAX_FILE_SIZE_MB}MB")
            st.write("**Supported formats:**")
            for ext in sorted(settings.SUPPORTED_EXTENSIONS):
                st.write(f"• {ext.upper()}")
            
            st.divider()
            
            # Processing settings
            st.subheader("Processing")
            st.write(f"**Model:** {settings.OPENAI_MODEL}")
            st.write(f"**Timeout:** {settings.PROCESSING_TIMEOUT_SECONDS}s")
            
            if settings.ENABLE_DEBUG_MODE:
                st.warning("🐛 Debug mode enabled")
    
    def render_file_upload(self) -> Optional[Dict[str, Any]]:
        """
        Render file upload interface and handle validation.
        
        Returns:
            Dictionary with file info if valid, None otherwise
        """
        st.header("📁 Upload Resume")
        
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=list(ext.lstrip('.') for ext in settings.SUPPORTED_EXTENSIONS),
            help=f"Maximum file size: {settings.MAX_FILE_SIZE_MB}MB"
        )
        
        if uploaded_file is not None:
            # Get file content
            file_content = uploaded_file.read()
            filename = uploaded_file.name
            file_size = len(file_content)
            
            # Display file info
            file_info = self.validator.get_file_info(filename, file_size)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", filename)
            with col2:
                st.metric("File Type", file_info["file_type"])
            with col3:
                st.metric("File Size", f"{file_info['size_mb']} MB")
            
            # Validate file
            is_valid, errors = self.validator.validate_uploaded_file(
                file_content, filename, uploaded_file.type
            )
            
            if not is_valid:
                st.error("❌ File validation failed:")
                for error in errors:
                    st.error(f"• {error}")
                return None
            
            st.success("✅ File validation passed!")
            
            return {
                "content": file_content,
                "filename": filename,
                "file_info": file_info,
                "mime_type": uploaded_file.type
            }
        
        return None
    
    def process_document(self, file_data: Dict[str, Any]) -> Optional[ParsedDocument]:
        """
        Process uploaded document using unstructured library.
        
        Args:
            file_data: Dictionary containing file content and metadata
            
        Returns:
            ParsedDocument with extracted elements or None if failed
        """
        try:
            with st.spinner("🔄 Processing document..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Parse document with unstructured
                status_text.text("📄 Extracting document elements...")
                progress_bar.progress(0.25)
                
                parsed_doc = self.document_parser.parse_document(
                    file_content=file_data["content"],
                    filename=file_data["filename"],
                    mime_type=file_data.get("mime_type")
                )
                
                if parsed_doc.parsing_warnings:
                    for warning in parsed_doc.parsing_warnings:
                        st.warning(f"⚠️ {warning}")
                
                # Step 2: Group elements into sections
                status_text.text("🗂️ Grouping content by sections...")
                progress_bar.progress(0.75)
                
                # Get the extracted elements from the parsed document
                elements = getattr(parsed_doc, '_raw_elements', [])
                
                processed_doc = self.content_processor.process_document(parsed_doc, elements)
                
                status_text.text("✅ Document processing complete!")
                progress_bar.progress(1.0)
                
                return processed_doc
                
        except Exception as e:
            st.error(f"❌ Document processing failed: {str(e)}")
            if settings.ENABLE_DEBUG_MODE:
                st.code(traceback.format_exc())
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
            st.error(f"❌ OpenAI API configuration error: {str(e)}")
            st.info("💡 Please set your OPENAI_API_KEY in the .env file")
            return False
        except Exception as e:
            st.error(f"❌ Failed to initialize GPT extractor: {str(e)}")
            return False
    
    def extract_structured_data(self, parsed_doc: ParsedDocument) -> Optional[ResumeSchema]:
        """
        Extract structured resume data using GPT-4o.
        
        Args:
            parsed_doc: Parsed document with grouped sections
            
        Returns:
            ResumeSchema with structured data or None if extraction fails
        """
        try:
            with st.spinner("🤖 Extracting structured data with GPT-4o..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Initialize GPT extractor
                status_text.text("🔧 Initializing AI extractor...")
                progress_bar.progress(0.1)
                
                if not self._initialize_gpt_extractor():
                    return None
                
                # Extract structured data
                status_text.text("🧠 Analyzing resume content with GPT-4o...")
                progress_bar.progress(0.5)
                
                structured_data = self.gpt_extractor.extract_structured_data(parsed_doc)
                
                if structured_data:
                    status_text.text("✅ Structured data extraction complete!")
                    progress_bar.progress(1.0)
                    
                    # Show extraction statistics
                    stats = self.gpt_extractor.get_extraction_stats(structured_data)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Skills Found", stats["total_skills"])
                    with col2:
                        st.metric("Work Experience", stats["total_work_experience"])
                    with col3:
                        st.metric("Education", stats["total_education"])
                    with col4:
                        st.metric("Total Experience", f"{stats['total_experience_months']} months")
                    
                    # Show token usage and cost information
                    self._render_token_usage_stats()
                    
                    return structured_data
                else:
                    status_text.text("❌ Structured data extraction failed")
                    st.error("Failed to extract structured data from resume")
                    return None
                    
        except Exception as e:
            st.error(f"❌ Structured data extraction failed: {str(e)}")
            if settings.ENABLE_DEBUG_MODE:
                st.code(traceback.format_exc())
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
            st.subheader("💰 GPT-4o Token Usage & Cost Analysis")
            
            # Current session stats
            st.markdown("**Current Extraction:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Input Tokens", 
                    f"{current_usage.input_tokens:,}",
                    help="Tokens sent to GPT-4o (prompts + resume content)"
                )
                st.caption(f"Cost: {current_usage.format_cost(current_usage.input_cost)}")
            
            with col2:
                if current_usage.cached_input_tokens > 0:
                    st.metric(
                        "Cached Tokens", 
                        f"{current_usage.cached_input_tokens:,}",
                        help="Cached input tokens (50% cost savings)"
                    )
                    st.caption(f"Cost: {current_usage.format_cost(current_usage.cached_input_cost)}")
                else:
                    st.metric("Cached Tokens", "0", help="No cached tokens used")
                    st.caption("Cost: $0.000000")
            
            with col3:
                st.metric(
                    "Output Tokens", 
                    f"{current_usage.output_tokens:,}",
                    help="Tokens generated by GPT-4o (structured JSON response)"
                )
                st.caption(f"Cost: {current_usage.format_cost(current_usage.output_cost)}")
            
            with col4:
                st.metric(
                    "Total Cost", 
                    current_usage.format_cost(current_usage.total_cost),
                    help="Total cost for this extraction"
                )
                st.caption(f"Total: {current_usage.total_tokens:,} tokens")
            
            # Cost breakdown details
            with st.expander("📊 Detailed Cost Breakdown", expanded=False):
                breakdown = current_usage.get_cost_breakdown()
                
                st.markdown("**Token Distribution:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.json({
                        "Input Tokens": breakdown["input_tokens"],
                        "Cached Input Tokens": breakdown["cached_input_tokens"],
                        "Output Tokens": breakdown["output_tokens"],
                        "Total Tokens": breakdown["total_tokens"]
                    })
                
                with col2:
                    st.markdown("**Cost Analysis:**")
                    st.markdown(f"• Input Cost: {breakdown['input_cost']}")
                    if breakdown["cached_input_tokens"] > 0:
                        st.markdown(f"• Cached Input Cost: {breakdown['cached_input_cost']} (50% savings)")
                    st.markdown(f"• Output Cost: {breakdown['output_cost']}")
                    st.markdown(f"• **Total Cost: {breakdown['total_cost']}**")
                
                st.markdown("**Pricing Reference (per 1M tokens):**")
                st.markdown("• Input: $2.50 | Cached Input: $1.25 | Output: $10.00")
            
            # Session totals if multiple extractions
            if len(self.gpt_extractor.token_tracker.usage_history) > 1:
                st.markdown("---")
                st.markdown("**Session Totals:**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Input", f"{total_usage.input_tokens:,}")
                with col2:
                    st.metric("Total Cached", f"{total_usage.cached_input_tokens:,}")
                with col3:
                    st.metric("Total Output", f"{total_usage.output_tokens:,}")
                with col4:
                    st.metric("Session Cost", total_usage.format_cost(total_usage.total_cost))
    
    def _render_skills_with_inference(self, skills: List) -> None:
        """
        Render skills with color-coded visualization to highlight inferred vs. explicit skills.
        
        Args:
            skills: List of Skill objects from the resume schema
        """
        # Add legend for color coding
        col1, col2 = st.columns([3, 1])
        with col2:
            st.markdown("""
            **Legend:**
            - 🟢 Explicitly mentioned
            - 🔵 Inferred by GPT-4o
            """)
        
        # Group skills by category
        skills_by_category = {}
        inferred_count = 0
        explicit_count = 0
        
        for skill in skills:
            category = skill.category or "General"
            if category not in skills_by_category:
                skills_by_category[category] = {"explicit": [], "inferred": []}
            
            if getattr(skill, 'isInferred', False):
                skills_by_category[category]["inferred"].append(skill)
                inferred_count += 1
            else:
                skills_by_category[category]["explicit"].append(skill)
                explicit_count += 1
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Skills", len(skills))
        with col2:
            st.metric("🟢 Explicit", explicit_count)
        with col3:
            st.metric("🔵 Inferred", inferred_count)
        
        # Render skills by category with color coding
        for category, skill_groups in skills_by_category.items():
            st.write(f"**{category}:**")
            
            # Create skill tags with color coding
            skill_tags = []
            
            # Add explicit skills (green)
            for skill in skill_groups["explicit"]:
                skill_tags.append(f":green[{skill.name}]")
            
            # Add inferred skills (blue) with inference info
            for skill in skill_groups["inferred"]:
                inferred_from = getattr(skill, 'inferredFrom', None)
                if inferred_from:
                    skill_tags.append(f":blue[{skill.name}] *(inferred from: {inferred_from})*")
                else:
                    skill_tags.append(f":blue[{skill.name}] *(inferred)*")
            
            # Display skills in a flowing format
            if skill_tags:
                st.markdown(" • ".join(skill_tags))
            
            st.write("")  # Add spacing between categories
        
        # Show detailed inference breakdown if there are inferred skills
        if inferred_count > 0:
            with st.expander(f"🔍 View GPT-4o Inference Details ({inferred_count} inferred skills)"):
                st.markdown("**GPT-4o Value-Add: Skills Inferred from Context**")
                
                for skill in skills:
                    if getattr(skill, 'isInferred', False):
                        inferred_from = getattr(skill, 'inferredFrom', 'context analysis')
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f":blue[**{skill.name}**]")
                        with col2:
                            st.markdown(f"*Inferred from: {inferred_from}*")
                            if skill.category:
                                st.caption(f"Category: {skill.category}")
    
    def render_results(self, parsed_resume: Optional[ResumeSchema] = None) -> None:
        """
        Render final parsing results in structured format (for GPT-4o output).
        
        Args:
            parsed_resume: Parsed resume data to display
        """
        st.header("🎯 Structured Resume Output")
        
        if parsed_resume is None:
            st.info("👆 Process a document first to see structured results here")
            return
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Structured View", "🔍 JSON Output", "⚠️ Metadata"])
        
        with tab1:
            self._render_structured_view(parsed_resume)
        
        with tab2:
            self._render_json_output(parsed_resume)
        
        with tab3:
            self._render_metadata(parsed_resume)
    
    def _render_structured_view(self, resume: ResumeSchema) -> None:
        """Render structured view of parsed resume."""
        # Contact Information
        st.subheader("👤 Contact Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {resume.contactInfo.fullName}")
            if resume.contactInfo.email:
                st.write(f"**Email:** {resume.contactInfo.email}")
            if resume.contactInfo.phone:
                st.write(f"**Phone:** {resume.contactInfo.phone}")
        
        with col2:
            if resume.contactInfo.location:
                location_parts = []
                if resume.contactInfo.location.city:
                    location_parts.append(resume.contactInfo.location.city)
                if resume.contactInfo.location.state:
                    location_parts.append(resume.contactInfo.location.state)
                if resume.contactInfo.location.country:
                    location_parts.append(resume.contactInfo.location.country)
                if location_parts:
                    st.write(f"**Location:** {', '.join(location_parts)}")
        
        # Summary
        if resume.summary:
            st.subheader("📝 Summary")
            st.write(resume.summary)
        
        # Skills with inference visualization
        if resume.skills:
            st.subheader("🛠️ Skills")
            self._render_skills_with_inference(resume.skills)
        
        # Work Experience
        if resume.workExperience:
            st.subheader("💼 Work Experience")
            for exp in resume.workExperience:
                with st.expander(f"{exp.jobTitle} at {exp.employer}"):
                    st.write(f"**Duration:** {exp.startDate} to {exp.endDate}")
                    if exp.location:
                        location_parts = []
                        if exp.location.city:
                            location_parts.append(exp.location.city)
                        if exp.location.state:
                            location_parts.append(exp.location.state)
                        if location_parts:
                            st.write(f"**Location:** {', '.join(location_parts)}")
                    st.write(f"**Description:** {exp.description}")
        
        # Education
        if resume.education:
            st.subheader("🎓 Education")
            for edu in resume.education:
                st.write(f"**{edu.degreeName}** ({edu.degreeType}) - {edu.schoolName}")
                if edu.graduationDate:
                    st.write(f"Graduated: {edu.graduationDate}")
    
    def _render_json_output(self, resume: ResumeSchema) -> None:
        """Render JSON output view."""
        st.subheader("Raw JSON Output")
        
        # Convert to dict and display
        resume_dict = resume.model_dump()
        json_str = json.dumps(resume_dict, indent=2, ensure_ascii=False)
        
        st.code(json_str, language="json")
        
        # Download button
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"parsed_resume_{resume.contactInfo.fullName.replace(' ', '_')}.json",
            mime="application/json"
        )
    
    def _render_metadata(self, resume: ResumeSchema) -> None:
        """Render metadata and warnings."""
        metadata = resume.parserMetadata
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**File Type:** {metadata.fileType}")
            st.write(f"**File Extension:** {metadata.fileExtension}")
            st.write(f"**Revision Date:** {metadata.revisionDate}")
        
        with col2:
            if metadata.culture:
                st.write(f"**Language:** {metadata.culture.language}")
                st.write(f"**Country:** {metadata.culture.country}")
        
        # Warnings
        if metadata.parserWarnings:
            st.subheader("⚠️ Parser Warnings")
            for warning in metadata.parserWarnings:
                st.warning(warning)
        else:
            st.success("✅ No parsing warnings")
    
    def run(self) -> None:
        """Main application entry point."""
        try:
            self.render_header()
            self.render_sidebar()
            
            # File upload section
            uploaded_file_data = self.render_file_upload()
            
            # Processing section
            if uploaded_file_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Parse Document", type="primary"):
                        # Process the document using unstructured library
                        parsed_doc = self.process_document(uploaded_file_data)
                        
                        if parsed_doc:
                            # Store in session state for persistence
                            st.session_state['parsed_document'] = parsed_doc
                            st.success("✅ Document processed successfully!")
                        else:
                            st.error("❌ Document processing failed")
                
                with col2:
                    # Only show GPT extraction button if document is parsed
                    parsed_doc = st.session_state.get('parsed_document')
                    if parsed_doc:
                        if st.button("🤖 Extract with GPT-4o", type="secondary"):
                            # Extract structured data using GPT-4o
                            structured_data = self.extract_structured_data(parsed_doc)
                            
                            if structured_data:
                                # Store in session state for persistence
                                st.session_state['structured_resume'] = structured_data
                                st.success("✅ Structured data extracted successfully!")
                            else:
                                st.error("❌ Structured data extraction failed")
            
            # Final structured results from GPT-4o
            structured_resume = st.session_state.get('structured_resume')
            parsed_doc = st.session_state.get('parsed_document')
            
            if structured_resume:
                self.render_results(structured_resume)
            elif parsed_doc:
                # Show placeholder if document is parsed but not extracted
                st.header("🎯 Structured Resume Output")
                st.info("👆 Click 'Extract with GPT-4o' to generate structured resume data")
            else:
                self.render_results()
            
        except Exception as e:
            st.error(f"❌ Application error: {str(e)}")
            if settings.ENABLE_DEBUG_MODE:
                st.code(traceback.format_exc())


def main():
    """Main entry point for Streamlit app."""
    app = ResumeParserUI()
    app.run()


if __name__ == "__main__":
    main()
