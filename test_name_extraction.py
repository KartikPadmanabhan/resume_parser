#!/usr/bin/env python3
"""
Test script to verify name extraction is working correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.document_parser import DocumentParser
from src.parsers.content_processor import ContentProcessor

def test_name_extraction():
    """Test name extraction with sample PDF."""
    print("🧪 Testing Name Extraction")
    print("=" * 50)
    
    # Test with sample PDF
    pdf_path = 'tests/sample_resumes/895963.pdf'
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    with open(pdf_path, 'rb') as f:
        content = f.read()
    
    parser = DocumentParser()
    processor = ContentProcessor()
    
    # Temporarily override the partition method to simulate OpenGL error
    original_partition = parser._partition_document
    def mock_opengl_error(*args, **kwargs):
        raise Exception('libGL.so.1: cannot open shared object file: No such file or directory')
    
    parser._partition_document = mock_opengl_error
    
    try:
        # Parse document (should trigger fallback)
        parsed_doc = parser.parse_document(content, '895963.pdf', 'application/pdf')
        print(f"✅ Fallback parsed: {parsed_doc.total_elements} elements")
        
        # Process content
        processed_doc = processor.process_document(parsed_doc, parsed_doc._raw_elements)
        print(f"✅ Processed: {len(processed_doc.grouped_sections)} sections")
        
        # Extract name from unknown section (should contain the name)
        name_found = False
        for section in processed_doc.grouped_sections:
            if section.section.value == 'unknown':
                print(f"📄 Unknown section content:")
                for element in section.elements[:5]:  # Show first 5 elements
                    print(f"   {element.text}")
                    # Check if this looks like a name
                    if 'Jim' in element.text or 'Hartz' in element.text:
                        name_found = True
                        print(f"✅ Found name: {element.text}")
        
        # Check contact section
        for section in processed_doc.grouped_sections:
            if section.section.value == 'contact':
                print(f"📧 Contact section content:")
                for element in section.elements:
                    print(f"   {element.text}")
        
        if name_found:
            print("\n🎉 Name extraction test PASSED!")
            print("The fallback parsing is correctly extracting 'Jim Hartz' instead of 'John Doe'")
            return True
        else:
            print("\n❌ Name extraction test FAILED!")
            print("Could not find the expected name 'Jim Hartz'")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    finally:
        # Restore original method
        parser._partition_document = original_partition

if __name__ == "__main__":
    success = test_name_extraction()
    sys.exit(0 if success else 1) 