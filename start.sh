#!/bin/bash

echo "🔍 STARTUP SCRIPT DEBUG: Starting application..."
echo "🔍 Current working directory: $(pwd)"
echo "🔍 Current user: $(whoami)"
echo "🔍 Python version: $(python --version)"

echo "🔍 ENVIRONMENT VARIABLES DEBUG:"
echo "PORT: '$PORT'"
echo "STREAMLIT_SERVER_PORT: '$STREAMLIT_SERVER_PORT'"
echo "RAILWAY_ENVIRONMENT: '$RAILWAY_ENVIRONMENT'"
echo "RAILWAY_PUBLIC_DOMAIN: '$RAILWAY_PUBLIC_DOMAIN'"

echo "🔍 PROCESS DEBUG:"
echo "PID: $$"
echo "Parent PID: $PPID"

echo "🔍 FILESYSTEM DEBUG:"
echo "Contents of current directory:"
ls -la

echo "🔍 STARTING STREAMLIT:"
echo "Command: streamlit run main.py"
exec streamlit run main.py 