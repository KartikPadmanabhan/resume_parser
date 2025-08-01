"""
Enhanced document parser leveraging unstructured library's full capabilities.
Extracts resume content as-is into a single string with spatial positioning.
Enhanced for 100% section coverage.
"""

import io
import tempfile
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from unstructured.partition.auto import partition
from unstructured.documents.elements import Element, ElementMetadata, CoordinatesMetadata
from unstructured.documents.coordinates import CoordinateSystem


@dataclass
class ResumeElement:
    """Resume element with enhanced spatial positioning."""
    text: str
    element_type: str
    coordinates: Optional[Dict[str, float]] = None
    page_number: Optional[int] = None
    spatial_position: Optional[str] = None  # header, body, footer
    confidence: float = 1.0
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False


class EnhancedUnstructuredParser:
    """
    Enhanced parser that extracts resume content as-is with spatial positioning.
    Goal: Extract all resume content into a single string preserving original structure.
    Enhanced for 100% section coverage using advanced unstructured features.
    """
    
    def __init__(self):
        """Initialize the enhanced parser."""
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.html', '.htm'}
        
        # Enhanced section keywords for better detection
        self.enhanced_sections = {
            'contact': ['contact', 'email', 'phone', 'address', 'linkedin', 'github', '@', 'ph:', 'tel:', 'mobile', 'cell'],
            'summary': ['summary', 'profile', 'overview', 'about', 'objective', 'professional summary', 'executive summary'],
            'experience': ['experience', 'employment', 'work', 'career', 'job', 'position', 'professional experience', 'work history'],
            'education': ['education', 'degree', 'university', 'college', 'school', 'academic', 'bachelor', 'master', 'phd', 'diploma'],
            'skills': ['skills', 'competencies', 'expertise', 'technologies', 'programming', 'languages', 'technical skills'],
            'certifications': ['certifications', 'certificates', 'licenses', 'certified', 'accreditation'],
            'projects': ['projects', 'portfolio', 'achievements', 'accomplishments', 'key projects'],
            'awards': ['awards', 'honors', 'recognition', 'achievements', 'distinctions']
        }
    
    def parse_resume_as_is(
        self,
        file_content: bytes,
        filename: str,
        strategy: str = "hi_res"
    ) -> str:
        """
        Parse resume and extract content as-is into a single string.
        Enhanced for 100% section coverage.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            strategy: Partitioning strategy ('fast', 'auto', 'hi_res', 'vlm')
            
        Returns:
            Single string containing all resume content as-is
        """
        file_extension = Path(filename).suffix.lower()
        
        try:
            # Create temporary file for unstructured processing
            with tempfile.NamedTemporaryFile(
                suffix=file_extension,
                delete=False
            ) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Set environment variables for OpenGL fallback
                os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
                os.environ.setdefault('MESA_GL_VERSION_OVERRIDE', '3.3')
                
                # Parse document using enhanced unstructured library
                elements = self._partition_document_enhanced(temp_file_path, strategy)
                
                if not elements:
                    return self._fallback_text_extraction(file_content, filename, file_extension)
                
                # Convert to resume elements with enhanced spatial positioning
                resume_elements = self._convert_to_enhanced_resume_elements(elements)
                
                # Generate as-is content string with enhanced section detection
                content_string = self._generate_enhanced_as_is_content(resume_elements)
                
                return content_string
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"Enhanced parsing failed: {str(e)}")
            # Return fallback content instead of failing completely
            return self._fallback_text_extraction(file_content, filename, file_extension)
    
    def _partition_document_enhanced(self, temp_file_path: str, strategy: str) -> List[Element]:
        """
        Enhanced document partitioning using advanced unstructured features.
        
        Args:
            temp_file_path: Path to temporary file
            strategy: Partitioning strategy
            
        Returns:
            List of unstructured elements with enhanced metadata
        """
        # Configure enhanced partitioning parameters for maximum coverage
        partition_kwargs = {
            'filename': temp_file_path,
            'strategy': strategy,
            'include_page_breaks': True,
            'infer_table_structure': True,
            'extract_images_in_pdf': True,
            'extract_image_block_types': ['Image', 'Table', 'Text'],
            'extract_image_block_to_payload': True,
            'starting_page_number': 1,
            'include_metadata': True,
            'include_coordinates': True
        }
        
        # Enhanced hi_res strategy with VLM capabilities
        if strategy == 'hi_res':
            partition_kwargs.update({
                'hi_res_model_name': 'yolox',  # Use YOLOX for better layout detection
                'include_metadata': True,
                'include_coordinates': True,
                'extract_images_in_pdf': True,
                'extract_image_block_types': ['Image', 'Table', 'Text'],
                'extract_image_block_to_payload': True
            })
        
        # Use VLM strategy for better understanding
        if strategy == 'vlm':
            partition_kwargs.update({
                'strategy': 'hi_res',
                'hi_res_model_name': 'yolox',
                'include_metadata': True,
                'include_coordinates': True,
                'extract_images_in_pdf': True,
                'extract_image_block_types': ['Image', 'Table', 'Text'],
                'extract_image_block_to_payload': True
            })
        
        return partition(**partition_kwargs)
    
    def _convert_to_enhanced_resume_elements(self, elements: List[Element]) -> List[ResumeElement]:
        """
        Convert unstructured elements to enhanced resume elements with better metadata.
        
        Args:
            elements: List of unstructured elements
            
        Returns:
            List of enhanced resume elements with spatial positioning
        """
        resume_elements = []
        
        for element in elements:
            try:
                # Extract text content as-is
                text_content = str(element)
                if not text_content.strip():
                    continue
                
                # Extract enhanced metadata
                metadata = self._extract_enhanced_metadata(element)
                
                # Determine spatial position based on coordinates
                spatial_position = self._determine_enhanced_spatial_position(metadata.get('coordinates'))
                
                # Extract font and styling information
                font_info = self._extract_font_information(metadata)
                
                # Create enhanced resume element
                resume_element = ResumeElement(
                    text=text_content,
                    element_type=element.category,
                    coordinates=metadata.get('coordinates'),
                    page_number=metadata.get('page_number'),
                    spatial_position=spatial_position,
                    confidence=metadata.get('detection_class_prob', 1.0),
                    font_size=font_info.get('font_size'),
                    is_bold=font_info.get('is_bold', False),
                    is_italic=font_info.get('is_italic', False)
                )
                
                resume_elements.append(resume_element)
                
            except Exception as e:
                print(f"Error converting element: {str(e)}")
                continue
        
        return resume_elements
    
    def _extract_enhanced_metadata(self, element: Element) -> Dict[str, Any]:
        """
        Extract enhanced metadata from unstructured element.
        
        Args:
            element: Unstructured element
            
        Returns:
            Dictionary with enhanced metadata
        """
        metadata = {}
        
        if hasattr(element, 'metadata') and element.metadata:
            try:
                # Extract page number
                if hasattr(element.metadata, 'page_number'):
                    metadata['page_number'] = element.metadata.page_number
                
                # Extract coordinates with enhanced precision
                if hasattr(element.metadata, 'coordinates') and element.metadata.coordinates:
                    coord_metadata = element.metadata.coordinates
                    if hasattr(coord_metadata, 'points'):
                        points = coord_metadata.points
                        if points and len(points) >= 4:
                            try:
                                # Extract bounding box coordinates with enhanced precision
                                x_coords = [point[0] for point in points if point and len(point) >= 2]
                                y_coords = [point[1] for point in points if point and len(point) >= 2]
                                
                                if x_coords and y_coords:
                                    metadata['coordinates'] = {
                                        'x1': min(x_coords),
                                        'y1': min(y_coords),
                                        'x2': max(x_coords),
                                        'y2': max(y_coords),
                                        'width': max(x_coords) - min(x_coords),
                                        'height': max(y_coords) - min(y_coords),
                                        'center_x': (min(x_coords) + max(x_coords)) / 2,
                                        'center_y': (min(y_coords) + max(y_coords)) / 2,
                                        'area': (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
                                    }
                            except (TypeError, ValueError, IndexError) as e:
                                print(f"Error extracting coordinates: {str(e)}")
                                # Set default coordinates to avoid comparison issues
                                metadata['coordinates'] = {
                                    'x1': 0.0, 'y1': 0.0, 'x2': 1.0, 'y2': 1.0,
                                    'width': 1.0, 'height': 1.0,
                                    'center_x': 0.5, 'center_y': 0.5, 'area': 1.0
                                }
                
                # Extract detection confidence
                if hasattr(element.metadata, 'detection_class_prob'):
                    metadata['detection_class_prob'] = element.metadata.detection_class_prob
                
                # Extract emphasized text information
                if hasattr(element.metadata, 'emphasized_text_contents'):
                    metadata['emphasized_text'] = element.metadata.emphasized_text_contents
                
                # Extract table information
                if hasattr(element.metadata, 'text_as_html'):
                    metadata['table_html'] = element.metadata.text_as_html
                
            except Exception as e:
                print(f"Error extracting enhanced metadata: {str(e)}")
        
        return metadata
    
    def _determine_enhanced_spatial_position(self, coordinates: Optional[Dict[str, float]]) -> Optional[str]:
        """
        Determine enhanced spatial position based on coordinates and content analysis.
        
        Args:
            coordinates: Coordinate dictionary
            
        Returns:
            Spatial position (header, body, footer)
        """
        if not coordinates or 'center_y' not in coordinates:
            return None
        
        # Normalize y coordinate (assuming 0-1 range)
        y_center = coordinates['center_y']
        
        # Enhanced position determination with better thresholds
        if y_center <= 0.15:  # Top 15% for header
            return 'header'
        elif y_center <= 0.85:  # Middle 70% for body
            return 'body'
        else:  # Bottom 15% for footer
            return 'footer'
    
    def _extract_font_information(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract font and styling information from metadata.
        
        Args:
            metadata: Element metadata
            
        Returns:
            Font information dictionary
        """
        font_info = {
            'font_size': None,
            'is_bold': False,
            'is_italic': False
        }
        
        # Extract from emphasized text information
        if 'emphasized_text' in metadata:
            emphasized_text = metadata['emphasized_text']
            if emphasized_text:
                # Analyze emphasized text for styling clues
                font_info['is_bold'] = any('bold' in str(tag).lower() for tag in emphasized_text)
                font_info['is_italic'] = any('italic' in str(tag).lower() for tag in emphasized_text)
        
        # Estimate font size from element height (if coordinates available)
        if 'coordinates' in metadata and metadata['coordinates']:
            height = metadata['coordinates'].get('height', 0)
            if height > 0:
                # Enhanced font size estimation
                font_info['font_size'] = height * 0.8  # Approximate conversion
        
        return font_info
    
    def _generate_enhanced_as_is_content(self, resume_elements: List[ResumeElement]) -> str:
        """
        Generate enhanced as-is content string with proper markdown formatting based on spatial analysis.
        
        Args:
            resume_elements: List of resume elements
            
        Returns:
            Single string with all resume content properly formatted with markdown
        """
        # Sort elements by spatial position (top to bottom, left to right)
        sorted_elements = self._sort_elements_spatially(resume_elements)
        
        # Build content string with proper markdown formatting
        content_parts = []
        
        # Track current position and section context
        current_page = None
        current_y = None
        current_x = None
        current_section = None
        in_content_block = False
        
        # Generic content classification - no hardcoded sections
        section_keywords = {}  # Not used in generic approach
        
        for i, element in enumerate(sorted_elements):
            # Get coordinates for spacing calculation
            coords = element.coordinates or {}
            element_y = coords.get('center_y', 0)
            element_x = coords.get('center_x', 0)
            element_page = element.page_number or 0
            
            # Handle page breaks
            if current_page is not None and element_page != current_page:
                content_parts.append("\n\n---\n\n")  # Markdown page separator
                current_y = None  # Reset Y position for new page
                current_section = None
                in_content_block = False
            
            # Handle vertical spacing (newlines)
            if current_y is not None:
                # Calculate vertical distance
                y_distance = abs(element_y - current_y)
                
                # Add appropriate spacing based on distance
                if y_distance > 80:  # Large gap - likely section break
                    content_parts.append("\n\n")
                    in_content_block = False
                elif y_distance > 40:  # Medium gap - paragraph break
                    content_parts.append("\n")
                elif y_distance > 15:  # Small gap - line break
                    content_parts.append("\n")
                # Very small gaps get no extra spacing
            
            # Handle horizontal spacing
            if current_x is not None and element_page == current_page:
                x_distance = abs(element_x - current_x)
                
                # Add horizontal spacing if elements are far apart
                if x_distance > 150:  # Significant horizontal gap
                    content_parts.append("    ")  # Tab-like spacing
                elif x_distance > 50:  # Medium gap
                    content_parts.append("  ")  # Double space
                # Small gaps get single space (handled by element text)
            
            # Clean and format the element text
            element_text = element.text.strip()
            
            # Skip empty elements
            if not element_text:
                continue
            
            # Determine the type of content this element represents
            content_type = self._classify_content_type(element, element_text, section_keywords, current_section, in_content_block)
            
            # Apply appropriate formatting based on content type
            if content_type == 'section_header':
                # This is a section header (e.g., "Professional Summary:")
                if content_parts and content_parts[-1] != "\n\n":
                    content_parts.append("\n")
                content_parts.append(f"## {element_text}\n")
                current_section = self._get_section_name(element_text, section_keywords)
                in_content_block = True
                
            elif content_type == 'subsection_header':
                # This is a subsection header (e.g., "Responsibilities:")
                if content_parts and content_parts[-1] != "\n\n":
                    content_parts.append("\n")
                content_parts.append(f"### {element_text}\n")
                in_content_block = True
                
            elif content_type == 'bullet_point':
                # This is a bullet point
                content_parts.append(f"• {element_text}")
                if not element_text.endswith(('.', ':', ';', '!', '?')):
                    content_parts.append(" ")
                    
            elif content_type == 'company_name':
                # This is a company name
                content_parts.append(f"**{element_text}**")
                if not element_text.endswith(('.', ':', ';', '!', '?')):
                    content_parts.append(" ")
                    
            elif content_type == 'date_range':
                # This is a date range
                content_parts.append(f"*{element_text}*")
                if not element_text.endswith(('.', ':', ';', '!', '?')):
                    content_parts.append(" ")
                    
            elif content_type == 'job_title':
                # This is a job title
                content_parts.append(f"**{element_text}**")
                if not element_text.endswith(('.', ':', ';', '!', '?')):
                    content_parts.append(" ")
                    
            else:
                # Regular content (not a header)
                content_parts.append(element_text)
                
                # Add space after text unless it ends with punctuation
                if not element_text.endswith(('.', ':', ';', '!', '?')):
                    content_parts.append(" ")
            
            # Update current position
            current_page = element_page
            current_y = element_y
            current_x = element_x
        
        # Join all parts
        raw_content = "".join(content_parts)
        
        # Post-process the content for better formatting
        
        # Clean up excessive whitespace while preserving intentional spacing
        # Replace multiple consecutive newlines with double newlines
        raw_content = re.sub(r'\n{3,}', '\n\n', raw_content)
        
        # Replace multiple consecutive spaces with single space
        raw_content = re.sub(r' {2,}', ' ', raw_content)
        
        # Clean up spacing around punctuation
        raw_content = re.sub(r'\s+([.,:;!?])', r'\1', raw_content)
        
        # Ensure proper spacing after punctuation
        raw_content = re.sub(r'([.,:;!?])([A-Za-z])', r'\1 \2', raw_content)
        
        # Clean up markdown formatting
        # Fix spacing around markdown headers
        raw_content = re.sub(r'([#]+)\s*([^#\n]+)', r'\1 \2', raw_content)
        
        # Fix bullet points
        raw_content = re.sub(r'^\s*e\s+', '• ', raw_content, flags=re.MULTILINE)
        
        # Fix email addresses with extra spaces
        raw_content = re.sub(r'([a-zA-Z0-9._%+-]+)\s*\.\s*([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})', r'\1.\2@\3.\4', raw_content)
        
        # Fix spacing around common separators
        raw_content = re.sub(r'\s*\|\s*', ' | ', raw_content)
        
        # Fix spacing around dates
        raw_content = re.sub(r'(\d{4})\s*[-–]\s*(\d{4}|present|current)', r'\1 – \2', raw_content)
        
        # Remove excessive newlines (more than 2 consecutive)
        raw_content = re.sub(r'\n{3,}', '\n\n', raw_content)
        
        # Fix spacing around parentheses
        raw_content = re.sub(r'\(\s+', '(', raw_content)
        raw_content = re.sub(r'\s+\)', ')', raw_content)
        
        # Final cleanup - remove leading/trailing whitespace
        raw_content = raw_content.strip()
        
        return raw_content
    
    def _classify_content_type(self, element: ResumeElement, text: str, section_keywords: Dict[str, List[str]], current_section: str, in_content_block: bool) -> str:
        """
        Generic content classification based on spatial analysis and content patterns.
        No hardcoded sections - works with any resume format.
        
        Returns: 'section_header', 'subsection_header', 'bullet_point', 'company_name', 
                'date_range', 'job_title', or 'content'
        """
        text_lower = text.lower()
        
        # 1. BULLET POINT DETECTION (most reliable)
        if self._is_likely_bullet_point(text):
            return 'bullet_point'
        
        # 2. DATE RANGE DETECTION (very reliable)
        if self._is_likely_date_range(text):
            return 'date_range'
        
        # 3. COMPANY NAME DETECTION (reliable patterns)
        if self._is_likely_company_name(text):
            return 'company_name'
        
        # 4. JOB TITLE DETECTION (reliable patterns)
        if self._is_likely_job_title(text):
            return 'job_title'
        
        # 5. SECTION HEADER DETECTION (based on formatting and context)
        if self._is_likely_section_header(element, text, current_section):
            return 'section_header'
        
        # 6. SUBSECTION HEADER DETECTION (short, ends with colon)
        if self._is_likely_subsection_header(element, text):
            return 'subsection_header'
        
        # 7. DEFAULT: Everything else is content
        return 'content'
    
    def _is_likely_section_header(self, element: ResumeElement, text: str, current_section: str) -> bool:
        """
        Detect section headers based on formatting and spatial analysis, not hardcoded keywords.
        """
        text_lower = text.lower()
        
        # Criteria for section headers:
        # 1. Short text (section headers are typically short)
        if len(text) > 50:
            return False
        
        # 2. Ends with colon (common for section headers)
        if text.endswith(':'):
            return True
        
        # 3. All caps or title case (common for section headers)
        if text.isupper() or (text[0].isupper() and text.lower() != text):
            # But not if it's clearly content
            if self._contains_content_indicators(text):
                return False
            return True
        
        # 4. Bold formatting (section headers are often bold)
        if element.is_bold:
            return True
        
        # 5. Larger font size (section headers often have larger fonts)
        if element.font_size and element.font_size > 12:
            return True
        
        # 6. Standalone text (not part of a sentence)
        if self._is_standalone_text(text):
            return True
        
        return False
    
    def _is_likely_subsection_header(self, element: ResumeElement, text: str) -> bool:
        """
        Detect subsection headers (like "Responsibilities:", "Skills:", etc.)
        """
        # Short text that ends with colon
        if len(text) < 30 and text.endswith(':'):
            return True
        
        # Bold short text
        if element.is_bold and len(text) < 30:
            return True
        
        return False
    
    def _contains_content_indicators(self, text: str) -> bool:
        """
        Check if text contains indicators that it's content, not a header.
        """
        text_lower = text.lower()
        
        # Content indicators (words that suggest this is descriptive content)
        content_words = [
            'experience', 'developed', 'implemented', 'managed', 'created', 'designed',
            'worked', 'used', 'utilized', 'skilled', 'proficient', 'expertise',
            'responsible', 'involved', 'participated', 'collaborated', 'led',
            'maintained', 'configured', 'deployed', 'integrated', 'optimized',
            'experienced', 'strong', 'deep', 'demonstrated', 'professional',
            'extensive', 'proficient', 'skilled', 'adept', 'substantial',
            'working', 'developing', 'creating', 'monitoring', 'involving',
            'using', 'utilizing', 'leveraged', 'architect', 'engineer',
            'certified', 'delivered', 'directed', 'served', 'maintained',
            'supported', 'scoped', 'boosted', 'handled', 'engineered',
            'shaped', 'cut', 'facilitated', 'redesigned', 'collaborated'
        ]
        
        for word in content_words:
            if word in text_lower:
                return True
        
        return False
    
    def _is_standalone_text(self, text: str) -> bool:
        """
        Check if text appears to be standalone (not part of a sentence).
        """
        # If text is very short and doesn't end with punctuation, likely standalone
        if len(text) < 20 and not text.endswith(('.', ':', ';', '!', '?')):
            return True
        
        # If text is all caps and short, likely standalone
        if text.isupper() and len(text) < 30:
            return True
        
        # If text doesn't contain common sentence words
        sentence_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with']
        text_lower = text.lower()
        
        has_sentence_indicators = any(indicator in text_lower for indicator in sentence_indicators)
        if not has_sentence_indicators and len(text) < 40:
            return True
        
        return False
    
    def _get_section_name(self, text: str, section_keywords: Dict[str, List[str]]) -> str:
        """Get the section name from text."""
        text_lower = text.lower()
        
        for section, keywords in section_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return section
        
        return None
    
    def _is_likely_job_title(self, text: str) -> bool:
        """Determine if text is likely a job title."""
        text_lower = text.lower()
        
        # Job title patterns
        job_title_patterns = [
            r'Developer$', r'Engineer$', r'Manager$', r'Lead$', r'Architect$',
            r'Analyst$', r'Consultant$', r'Specialist$', r'Coordinator$',
            r'Director$', r'Supervisor$', r'Administrator$', r'Designer$'
        ]
        
        for pattern in job_title_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Common job title words
        job_title_words = [
            'developer', 'engineer', 'manager', 'lead', 'architect', 'analyst',
            'consultant', 'specialist', 'coordinator', 'director', 'supervisor',
            'administrator', 'designer', 'programmer', 'coder', 'analyst'
        ]
        
        for word in job_title_words:
            if word in text_lower:
                return True
        
        return False
    
    def _sort_elements_spatially(self, elements: List[ResumeElement]) -> List[ResumeElement]:
        """
        Sort elements by spatial position (top to bottom, left to right).
        
        Args:
            elements: List of resume elements
            
        Returns:
            Sorted list of elements
        """
        def sort_key(element):
            # Primary sort by page number
            page = element.page_number or 0
            
            # Secondary sort by y-coordinate (top to bottom)
            y_coord = 0
            if element.coordinates and 'center_y' in element.coordinates:
                y_coord = element.coordinates['center_y'] or 0
            
            # Tertiary sort by x-coordinate (left to right)
            x_coord = 0
            if element.coordinates and 'center_x' in element.coordinates:
                x_coord = element.coordinates['center_x'] or 0
            
            return (page, y_coord, x_coord)
        
        return sorted(elements, key=sort_key)
    
    def _is_section_header(self, text: str, section_keywords: Dict[str, List[str]]) -> bool:
        """Determine if text is a section header."""
        text_lower = text.lower()
        
        for section, keywords in section_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return True
        
        return False
    
    def _is_likely_bullet_point(self, text: str) -> bool:
        """Determine if text is likely a bullet point."""
        # Check for common bullet point patterns
        bullet_patterns = [
            r'^[•·▪▫◦‣⁃]\s+',  # Unicode bullets
            r'^[-*+]\s+',       # Markdown bullets
            r'^[a-z]\)\s+',     # Letter bullets
            r'^[0-9]+\.\s+',    # Numbered bullets
            r'^e\s+',           # OCR artifacts
            r'^¢\s+',           # OCR artifacts
            r'^\s*[•·▪▫◦‣⁃]\s+',  # Unicode bullets with leading spaces
            r'^\s*[-*+]\s+',       # Markdown bullets with leading spaces
        ]
        
        for pattern in bullet_patterns:
            if re.match(pattern, text):
                return True
        
        # Check for common bullet point content patterns
        bullet_content_patterns = [
            r'^[A-Z][a-z]+\s+',  # Starts with capitalized word
            r'^[A-Z][A-Z\s]+\s+',  # Starts with all caps
        ]
        
        # If text starts with these patterns and is short, likely a bullet
        for pattern in bullet_content_patterns:
            if re.match(pattern, text) and len(text) < 100:
                return True
        
        return False
    
    def _is_likely_company_name(self, text: str) -> bool:
        """Determine if text is likely a company name."""
        # Check for common company name patterns
        company_patterns = [
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+',  # Two word capitalized
            r'^[A-Z][A-Z\s]+$',              # All caps
            r'.*Inc\.?$',                     # Ends with Inc
            r'.*Corp\.?$',                    # Ends with Corp
            r'.*LLC$',                        # Ends with LLC
            r'.*Ltd\.?$',                     # Ends with Ltd
        ]
        
        for pattern in company_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _is_likely_date_range(self, text: str) -> bool:
        """Determine if text is likely a date range."""
        # Check for date range patterns
        date_patterns = [
            r'\d{4}\s*[-–]\s*\d{4}',         # YYYY - YYYY
            r'\d{4}\s*[-–]\s*present',       # YYYY - present
            r'\d{4}\s*[-–]\s*current',       # YYYY - current
            r'\w+\s+\d{4}\s*[-–]\s*\w+\s+\d{4}',  # Month YYYY - Month YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _fallback_text_extraction(self, file_content: bytes, filename: str, file_extension: str) -> str:
        """
        Enhanced fallback text extraction when advanced parsing fails.
        Uses unstructured library to handle any file format.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            file_extension: File extension
            
        Returns:
            Basic text content
        """
        try:
            # Use unstructured library to parse any file format
            from unstructured.partition.auto import partition
            from io import BytesIO
            import tempfile
            import os
            
            # Create a temporary file with the correct extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Use unstructured to partition the document
                elements = partition(temp_file_path)
                
                # Extract text from all elements with proper formatting
                text_parts = []
                for element in elements:
                    if hasattr(element, 'text') and element.text.strip():
                        # Clean and format the text
                        clean_text = element.text.strip()
                        if clean_text:
                            text_parts.append(clean_text)
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                # Combine all text parts with proper spacing
                text_content = "\n\n".join(text_parts)
                
                if text_content.strip():
                    return text_content
                
            except Exception as e:
                print(f"Error parsing with unstructured: {str(e)}")
                # Clean up temp file on error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            # If unstructured fails, try basic text extraction
            text_content = file_content.decode('utf-8', errors='ignore')
            if not text_content.strip():
                # Try other encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text_content = file_content.decode(encoding, errors='ignore')
                        if text_content.strip():
                            break
                    except:
                        continue
            
            # If we still don't have meaningful text, create a basic structure
            if not text_content.strip() or len(text_content.strip()) < 50:
                # Create a basic resume structure for GPT to work with
                text_content = f"""
RESUME CONTENT (Basic Structure)
{'='*50}

CONTACT INFORMATION
Name: [Extracted from {filename}]
Email: [To be extracted]
Phone: [To be extracted]

SUMMARY
[Professional summary to be extracted from document]

EXPERIENCE
[Work experience to be extracted from document]

EDUCATION
[Education details to be extracted from document]

SKILLS
[Skills to be extracted from document]

Note: This is a fallback structure. The original document ({filename}) could not be fully parsed, but GPT will attempt to extract information from the available content.
"""
            
            return f"RESUME CONTENT (Enhanced Fallback)\n{'='*50}\n\n{text_content}"
            
        except Exception as e:
            return f"""
RESUME CONTENT (Error Recovery)
{'='*50}

CONTACT INFORMATION
Name: [To be extracted from {filename}]
Email: [To be extracted]
Phone: [To be extracted]

SUMMARY
[Professional summary to be extracted]

EXPERIENCE
[Work experience to be extracted]

EDUCATION
[Education details to be extracted]

SKILLS
[Skills to be extracted]

Note: Document parsing encountered an error: {str(e)}
GPT will attempt to extract any available information from the document.
""" 