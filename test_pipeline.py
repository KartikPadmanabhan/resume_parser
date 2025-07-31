#!/usr/bin/env python3
"""
Comprehensive test script to validate the entire resume parsing pipeline.
Tests both passed and failed directories to ensure no regressions and all issues are resolved.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.document_parser import DocumentParser
from src.parsers.content_processor import ContentProcessor
from src.agents.gpt_extractor import GPTExtractor
from config.settings import settings

def test_pipeline():
    """Test the entire resume parsing pipeline on both passed and failed directories."""
    
    print("🧪 Testing Resume Parsing Pipeline")
    print("=" * 60)
    
    # Test directories
    passed_dir = "tests/sample_resumes/passed"
    failed_dir = "tests/sample_resumes/failed"
    
    results = {
        "passed": {"total": 0, "success": 0, "failed": 0, "details": []},
        "failed": {"total": 0, "success": 0, "failed": 0, "details": []}
    }
    
    # Test passed directory (should work without issues)
    print(f"\n📁 Testing PASSED Directory: {passed_dir}")
    print("-" * 40)
    
    if os.path.exists(passed_dir):
        passed_files = [f for f in os.listdir(passed_dir) if f.endswith(('.pdf', '.docx', '.txt'))]
        results["passed"]["total"] = len(passed_files)
        
        for filename in passed_files:
            file_path = os.path.join(passed_dir, filename)
            success, details = test_single_resume(file_path, "passed")
            
            if success:
                results["passed"]["success"] += 1
            else:
                results["passed"]["failed"] += 1
            
            results["passed"]["details"].append(details)
    else:
        print(f"⚠️  Directory not found: {passed_dir}")
    
    # Test failed directory (should now work with fixes)
    print(f"\n📁 Testing FAILED Directory: {failed_dir}")
    print("-" * 40)
    
    if os.path.exists(failed_dir):
        failed_files = [f for f in os.listdir(failed_dir) if f.endswith(('.pdf', '.docx', '.txt'))]
        results["failed"]["total"] = len(failed_files)
        
        for filename in failed_files:
            file_path = os.path.join(failed_dir, filename)
            success, details = test_single_resume(file_path, "failed")
            
            if success:
                results["failed"]["success"] += 1
            else:
                results["failed"]["failed"] += 1
            
            results["failed"]["details"].append(details)
    else:
        print(f"⚠️  Directory not found: {failed_dir}")
    
    # Print summary
    print_summary(results)

def test_single_resume(file_path: str, category: str) -> Tuple[bool, Dict]:
    """Test a single resume file through the entire pipeline."""
    
    filename = os.path.basename(file_path)
    print(f"\n📄 Testing: {filename}")
    
    try:
        # Step 1: Document parsing
        parser = DocumentParser()
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        parsed_doc = parser.parse_document(file_content, filename)
        
        if not parsed_doc or not parsed_doc._raw_elements:
            return False, {
                "filename": filename,
                "category": category,
                "error": "Document parsing failed - no elements extracted",
                "step": "parsing"
            }
        
        # Step 2: Content processing
        processor = ContentProcessor()
        processed_doc = processor.process_document(parsed_doc, parsed_doc._raw_elements)
        
        if not processed_doc or not processed_doc.grouped_sections:
            return False, {
                "filename": filename,
                "category": category,
                "error": "Content processing failed - no sections found",
                "step": "processing"
            }
        
        # Step 3: GPT extraction
        extractor = GPTExtractor()
        resume_schema = extractor.extract_structured_data(processed_doc)
        
        if not resume_schema:
            return False, {
                "filename": filename,
                "category": category,
                "error": "GPT extraction failed",
                "step": "extraction"
            }
        
        # Step 4: Validate extracted data
        validation_result = validate_extracted_data(resume_schema, filename, category)
        
        if validation_result["success"]:
            print(f"   ✅ SUCCESS: {validation_result['message']}")
            return True, {
                "filename": filename,
                "category": category,
                "success": True,
                "message": validation_result["message"],
                "stats": validation_result["stats"]
            }
        else:
            print(f"   ⚠️  PARTIAL: {validation_result['message']}")
            return False, {
                "filename": filename,
                "category": category,
                "error": validation_result["message"],
                "step": "validation"
            }
        
    except Exception as e:
        error_msg = f"Pipeline error: {str(e)}"
        print(f"   ❌ FAILED: {error_msg}")
        return False, {
            "filename": filename,
            "category": category,
            "error": error_msg,
            "step": "pipeline"
        }

def validate_extracted_data(resume_schema, filename: str, category: str) -> Dict:
    """Validate the extracted resume data."""
    
    stats = {
        "contact_info": bool(resume_schema.contactInfo and resume_schema.contactInfo.fullName),
        "skills_count": len(resume_schema.skills) if resume_schema.skills else 0,
        "education_count": len(resume_schema.education) if resume_schema.education else 0,
        "work_experience_count": len(resume_schema.workExperience) if resume_schema.workExperience else 0,
        "certifications_count": len(resume_schema.certifications) if resume_schema.certifications else 0
    }
    
    # Basic validation
    if not resume_schema.contactInfo or not resume_schema.contactInfo.fullName:
        return {
            "success": False,
            "message": "No contact information extracted",
            "stats": stats
        }
    
    if not resume_schema.workExperience:
        return {
            "success": False,
            "message": "No work experience extracted",
            "stats": stats
        }
    
    # Special validation for failed category (should have multiple employment positions)
    if category == "failed" and filename == "18794299.docx":
        # This specific file should have multiple employment positions
        if len(resume_schema.workExperience) < 2:
            return {
                "success": False,
                "message": f"Expected multiple employment positions, got {len(resume_schema.workExperience)}",
                "stats": stats
            }
        
        # Check for specific companies
        employers = [work.employer.lower() for work in resume_schema.workExperience if work.employer]
        expected_companies = ["cvs", "sentara", "cme"]
        found_companies = [company for company in expected_companies if any(company in emp for emp in employers)]
        
        if len(found_companies) < 2:
            return {
                "success": False,
                "message": f"Expected at least 2 companies from {expected_companies}, found {found_companies}",
                "stats": stats
            }
    
    # Success message
    message = f"Extracted {stats['work_experience_count']} positions, {stats['skills_count']} skills, {stats['education_count']} education"
    
    return {
        "success": True,
        "message": message,
        "stats": stats
    }

def print_summary(results: Dict):
    """Print a comprehensive summary of test results."""
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for category, result in results.items():
        print(f"\n📁 {category.upper()} Directory:")
        print(f"   Total files: {result['total']}")
        print(f"   ✅ Success: {result['success']}")
        print(f"   ❌ Failed: {result['failed']}")
        print(f"   📈 Success rate: {(result['success'] / result['total'] * 100):.1f}%" if result['total'] > 0 else "   📈 Success rate: N/A")
        
        if result['failed'] > 0:
            print("   🔍 Failed files:")
            for detail in result['details']:
                if not detail.get('success', False):
                    print(f"      - {detail['filename']}: {detail.get('error', 'Unknown error')}")
    
    # Overall summary
    total_files = results["passed"]["total"] + results["failed"]["total"]
    total_success = results["passed"]["success"] + results["failed"]["success"]
    total_failed = results["passed"]["failed"] + results["failed"]["failed"]
    
    print(f"\n🎯 OVERALL SUMMARY:")
    print(f"   Total files tested: {total_files}")
    print(f"   ✅ Total success: {total_success}")
    print(f"   ❌ Total failed: {total_failed}")
    print(f"   📈 Overall success rate: {(total_success / total_files * 100):.1f}%" if total_files > 0 else "   📈 Overall success rate: N/A")
    
    # Specific validation for the problematic file
    failed_details = results["failed"]["details"]
    for detail in failed_details:
        if detail.get('filename') == '18794299.docx':
            if detail.get('success', False):
                print(f"\n🎉 SUCCESS: The problematic file 18794299.docx is now working correctly!")
                print(f"   - Extracted {detail.get('stats', {}).get('work_experience_count', 0)} employment positions")
            else:
                print(f"\n⚠️  WARNING: The problematic file 18794299.docx still has issues:")
                print(f"   - Error: {detail.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_pipeline() 