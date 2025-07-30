#!/usr/bin/env python3
"""
Test script to verify fallback parsing works when OpenGL libraries are not available.
This simulates the Railway deployment environment.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.document_parser import DocumentParser

def test_fallback_parsing():
    """Test fallback parsing with sample resume."""
    print("🧪 Testing Fallback Parsing")
    print("=" * 50)
    
    # Initialize parser
    parser = DocumentParser()
    
    # Test with sample resume text
    sample_content = """John Smith
Software Engineer
john.smith@email.com
(555) 123-4567
San Francisco, CA

SUMMARY
Experienced software engineer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies.

SKILLS
Programming Languages: Python, JavaScript, Java, C++
Web Technologies: React, Node.js, Django, Flask
Databases: PostgreSQL, MongoDB, Redis
Cloud Platforms: AWS, Google Cloud Platform
Tools: Docker, Kubernetes, Git, Jenkins

EXPERIENCE

Senior Software Engineer
Tech Solutions Inc. | San Francisco, CA | 2021 - Present
• Led development of microservices architecture serving 1M+ users
• Implemented CI/CD pipelines reducing deployment time by 60%
• Mentored junior developers and conducted code reviews

Software Engineer
StartupXYZ | San Francisco, CA | 2019 - 2021
• Developed full-stack web applications using React and Django
• Optimized database queries improving application performance by 40%
• Participated in agile development processes and sprint planning

EDUCATION

Bachelor of Science in Computer Science
University of California, Berkeley | Berkeley, CA | 2019
GPA: 3.8/4.0

CERTIFICATIONS
AWS Certified Solutions Architect - Associate | 2022
Google Cloud Professional Developer | 2021"""
    
    # Convert to bytes
    file_content = sample_content.encode('utf-8')
    
    try:
        # Test parsing
        print("📄 Testing document parsing...")
        parsed_doc = parser.parse_document(
            file_content=file_content,
            filename="test_resume.txt",
            mime_type="text/plain"
        )
        
        print(f"✅ Parsing successful!")
        print(f"📊 Document stats:")
        print(f"   - Total elements: {parsed_doc.total_elements}")
        print(f"   - File type: {parsed_doc.file_type}")
        print(f"   - Warnings: {len(parsed_doc.parsing_warnings)}")
        
        if parsed_doc.parsing_warnings:
            print("⚠️  Warnings:")
            for warning in parsed_doc.parsing_warnings:
                print(f"   - {warning}")
        
        # Test fallback parsing by simulating OpenGL error
        print("\n🔄 Testing fallback parsing...")
        
        # Temporarily modify the partition function to raise OpenGL error
        original_partition = parser._partition_document
        
        def mock_partition_with_opengl_error(*args, **kwargs):
            raise Exception("libGL.so.1: cannot open shared object file: No such file or directory")
        
        parser._partition_document = mock_partition_with_opengl_error
        
        # Test fallback parsing
        fallback_doc = parser.parse_document(
            file_content=file_content,
            filename="test_resume.txt",
            mime_type="text/plain"
        )
        
        print(f"✅ Fallback parsing successful!")
        print(f"📊 Fallback document stats:")
        print(f"   - Total elements: {fallback_doc.total_elements}")
        print(f"   - Warnings: {len(fallback_doc.parsing_warnings)}")
        
        if fallback_doc.parsing_warnings:
            print("⚠️  Fallback warnings:")
            for warning in fallback_doc.parsing_warnings:
                print(f"   - {warning}")
        
        # Restore original function
        parser._partition_document = original_partition
        
        print("\n🎉 All tests passed! Fallback parsing is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_fallback_parsing()
    sys.exit(0 if success else 1) 