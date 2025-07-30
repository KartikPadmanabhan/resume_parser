"""
Minimalistic test app with PORT forwarding debug messages.
"""

import streamlit as st
import os
import sys

def debug_port_info():
    """Print debug information about port configuration."""
    st.write("🔍 **DEBUG: PORT CONFIGURATION**")
    st.write(f"PORT environment variable: '{os.environ.get('PORT', 'NOT SET')}'")
    st.write(f"STREAMLIT_SERVER_PORT: '{os.environ.get('STREAMLIT_SERVER_PORT', 'NOT SET')}'")
    st.write(f"RAILWAY_ENVIRONMENT: '{os.environ.get('RAILWAY_ENVIRONMENT', 'NOT SET')}'")
    st.write(f"RAILWAY_PUBLIC_DOMAIN: '{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'NOT SET')}'")
    st.write(f"Python executable: {sys.executable}")
    st.write(f"Working directory: {os.getcwd()}")
    st.write("---")

def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="PORT Debug App",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 PORT Debug Application")
    st.write("This is a minimalistic app to debug PORT forwarding issues.")
    
    # Debug information
    debug_port_info()
    
    # Simple test content
    st.header("Test Content")
    st.write("If you can see this, the app is running successfully!")
    
    # Environment variables display
    st.header("All Environment Variables")
    for key, value in os.environ.items():
        if 'PORT' in key or 'RAILWAY' in key or 'STREAMLIT' in key:
            st.code(f"{key}={value}")
    
    st.success("✅ App is running!")

if __name__ == "__main__":
    main()
