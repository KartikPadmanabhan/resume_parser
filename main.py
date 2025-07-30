"""
Main entry point for the Resume Parser application.
Run this file to start the Streamlit web interface.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the Streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main()
