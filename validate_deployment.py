#!/usr/bin/env python3
"""
Deployment Validation Script for Railway.app
Validates that all dependencies and configurations are ready for deployment.
"""

import sys
import json
import subprocess
import importlib
from pathlib import Path
from typing import List, Tuple

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def check_python_dependencies() -> List[Tuple[str, bool]]:
    """Check if all required Python packages are installed."""
    # Map package names to their import names
    required_packages = {
        'streamlit': 'streamlit',
        'openai': 'openai',
        'tiktoken': 'tiktoken',
        'pydantic': 'pydantic',
        'unstructured': 'unstructured',
        'python-magic': 'magic',
        'pytesseract': 'pytesseract',
        'python-dotenv': 'dotenv'
    }
    
    results = []
    for package_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            results.append((package_name, True))
        except ImportError:
            results.append((package_name, False))
    
    return results

def check_system_dependencies() -> List[Tuple[str, bool]]:
    """Check if system dependencies are available."""
    system_deps = ['pdfinfo', 'tesseract', 'file']
    results = []
    
    for dep in system_deps:
        try:
            result = subprocess.run(['which', dep], capture_output=True, text=True)
            results.append((dep, result.returncode == 0))
        except Exception:
            results.append((dep, False))
    
    return results

def validate_railway_config() -> bool:
    """Validate Railway configuration files."""
    required_files = [
        'railway.json',
        'nixpacks.toml',
        'Procfile',
        '.railwayignore',
        'requirements.txt',
        'main.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not check_file_exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    # Validate railway.json structure
    try:
        with open('railway.json', 'r') as f:
            config = json.load(f)
            
        required_keys = ['build', 'deploy']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing '{key}' section in railway.json")
                return False
                
        if 'startCommand' not in config['deploy']:
            print("❌ Missing 'startCommand' in deploy section")
            return False
            
    except json.JSONDecodeError:
        print("❌ Invalid JSON in railway.json")
        return False
    except FileNotFoundError:
        print("❌ railway.json not found")
        return False
    
    return True

def main():
    """Main validation function."""
    print("🚀 Railway.app Deployment Validation")
    print("=" * 50)
    
    # Check deployment files
    print("\n📁 Checking deployment configuration files...")
    config_valid = validate_railway_config()
    if config_valid:
        print("✅ All deployment configuration files are present and valid")
    else:
        print("❌ Deployment configuration validation failed")
        return False
    
    # Check Python dependencies
    print("\n🐍 Checking Python dependencies...")
    python_deps = check_python_dependencies()
    python_success = True
    for package, installed in python_deps:
        status = "✅" if installed else "❌"
        print(f"  {status} {package}")
        if not installed:
            python_success = False
    
    if not python_success:
        print("\n❌ Some Python dependencies are missing. Run: pip install -r requirements.txt")
        return False
    
    # Check system dependencies
    print("\n🔧 Checking system dependencies...")
    system_deps = check_system_dependencies()
    system_success = True
    for dep, available in system_deps:
        status = "✅" if available else "⚠️"
        print(f"  {status} {dep}")
        if not available:
            system_success = False
    
    if not system_success:
        print("\n⚠️  Some system dependencies are missing locally.")
        print("   This is OK for Railway deployment (nixpacks.toml handles this)")
        print("   For local development, install: brew install poppler tesseract libmagic")
    
    # Check environment variables
    print("\n🔑 Checking environment configuration...")
    env_example_exists = check_file_exists('.env.example')
    env_exists = check_file_exists('.env')
    
    if env_example_exists:
        print("  ✅ .env.example found")
    else:
        print("  ❌ .env.example missing")
    
    if env_exists:
        print("  ✅ .env found (for local development)")
    else:
        print("  ⚠️  .env not found (create for local development)")
    
    print("\n🎉 Deployment Validation Summary:")
    print("=" * 50)
    
    if config_valid and python_success:
        print("✅ READY FOR RAILWAY DEPLOYMENT!")
        print("\nNext steps:")
        print("1. Push code to GitHub repository")
        print("2. Connect repository to Railway.app")
        print("3. Set OPENAI_API_KEY environment variable in Railway dashboard")
        print("4. Deploy!")
        return True
    else:
        print("❌ NOT READY FOR DEPLOYMENT")
        print("Please fix the issues above before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
