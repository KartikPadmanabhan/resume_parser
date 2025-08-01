#!/usr/bin/env python3
"""
Minimal test for the enhanced unstructured parser.
Tests the generic content classification and markdown formatting.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.enhanced_unstructured_parser import EnhancedUnstructuredParser

def test_enhanced_parser():
    """Test the enhanced parser with sample files."""
    
    # Test files
    test_files = [
        "tests/sample_resumes/failed/18794299.docx",
        "tests/sample_resumes/passed/895963.pdf"
    ]
    
    parser = EnhancedUnstructuredParser()
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
            
        print(f"\n{'='*80}")
        print(f"📄 TESTING: {file_path}")
        print(f"{'='*80}")
        
        try:
            # Read the file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Parse with enhanced parser
            result = parser.parse_resume_as_is(file_content, os.path.basename(file_path))
            
            print(f"✅ Parsed successfully")
            print(f"📊 Output length: {len(result)} characters")
            print(f"📝 First 500 characters:")
            print("-" * 50)
            print(result[:500])
            print("-" * 50)
            
            # Check for markdown formatting
            markdown_features = {
                'Headers (##)': result.count('##'),
                'Subheaders (###)': result.count('###'),
                'Bold text (**)': result.count('**'),
                'Italic text (*)': result.count('*'),
                'Bullet points (•)': result.count('•'),
                'Page separators (---)': result.count('---')
            }
            
            print(f"\n🔍 Markdown Features:")
            for feature, count in markdown_features.items():
                print(f"  {feature}: {count}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_parser() 