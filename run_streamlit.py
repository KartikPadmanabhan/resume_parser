#!/usr/bin/env python3
"""
Railway-compatible Streamlit launcher script.
Handles PORT environment variable properly to avoid Railway deployment issues.
"""

import os
import sys
import subprocess

def main():
    # Get the PORT from environment, default to 8501 for local development
    port = os.environ.get('PORT', '8501')
    
    # Validate that port is numeric
    try:
        port_num = int(port)
        if port_num <= 0 or port_num > 65535:
            raise ValueError(f"Port {port_num} is out of valid range")
    except (ValueError, TypeError):
        print(f"Warning: Invalid PORT '{port}', using default 8501")
        port = '8501'
    
    # Clear any Streamlit environment variables that might interfere
    streamlit_env_vars = [
        'STREAMLIT_SERVER_PORT',
        'STREAMLIT_SERVER_ADDRESS',
        'STREAMLIT_SERVER_HEADLESS',
        'STREAMLIT_SERVER_ENABLE_CORS',
        'STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'
    ]
    
    for var in streamlit_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Build the streamlit command
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'main.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    print(f"Starting Streamlit on port {port}")
    print(f"Command: {' '.join(cmd)}")
    
    # Execute streamlit
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Streamlit stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()
