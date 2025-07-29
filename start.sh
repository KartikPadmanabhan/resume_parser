#!/bin/bash

echo "=== STARTUP SCRIPT DEBUG ==="
echo "Starting startup script..."

# Debug: Show all environment variables that might affect port
echo "=== ENVIRONMENT VARIABLES DEBUG ==="
echo "PORT (raw): '$PORT'"
echo "STREAMLIT_SERVER_PORT (raw): '$STREAMLIT_SERVER_PORT'"
echo "RAILWAY_ENVIRONMENT: '$RAILWAY_ENVIRONMENT'"
echo "RAILWAY_PUBLIC_DOMAIN: '$RAILWAY_PUBLIC_DOMAIN'"

# Clear the problematic STREAMLIT_SERVER_PORT environment variable
echo "=== CLEARING STREAMLIT_SERVER_PORT ==="
unset STREAMLIT_SERVER_PORT
echo "STREAMLIT_SERVER_PORT after unset: '$STREAMLIT_SERVER_PORT'"

# Show final environment state
echo "=== FINAL ENVIRONMENT STATE ==="
echo "PORT: '$PORT'"
echo "STREAMLIT_SERVER_PORT: '$STREAMLIT_SERVER_PORT'"

# Start Streamlit
echo "=== STARTING STREAMLIT ==="
echo "Command: exec streamlit run main.py"
exec streamlit run main.py 