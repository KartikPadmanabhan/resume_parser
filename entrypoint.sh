#!/bin/bash

# Railway-compatible Streamlit entrypoint script
# Handles PORT environment variable expansion properly in Docker

echo "=== RAILWAY DEPLOYMENT DEBUG ==="
echo "Starting Streamlit application..."

# Debug: Show all environment variables that might affect port
echo "=== ENVIRONMENT VARIABLES DEBUG ==="
echo "PORT (raw): '$PORT'"
echo "STREAMLIT_SERVER_PORT (raw): '$STREAMLIT_SERVER_PORT'"
echo "RAILWAY_ENVIRONMENT: '$RAILWAY_ENVIRONMENT'"
echo "RAILWAY_PUBLIC_DOMAIN: '$RAILWAY_PUBLIC_DOMAIN'"

# Get the actual port number from Railway
# Railway provides PORT as an environment variable
ACTUAL_PORT=${PORT:-8501}

echo "=== PORT PROCESSING ==="
echo "Railway provided PORT: '$PORT'"
echo "Using actual port: '$ACTUAL_PORT'"

# Clear ALL Streamlit environment variables that might interfere
echo "=== CLEARING STREAMLIT VARIABLES ==="
unset STREAMLIT_SERVER_PORT
unset STREAMLIT_SERVER_ADDRESS
unset STREAMLIT_SERVER_HEADLESS
unset STREAMLIT_SERVER_ENABLE_CORS
unset STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION
unset STREAMLIT_BROWSER_GATHER_USAGE_STATS
unset STREAMLIT_SERVER_FILE_WATCHER_TYPE

echo "Cleared all Streamlit environment variables"

echo "=== FINAL CONFIGURATION ==="
echo "Final ACTUAL_PORT: '$ACTUAL_PORT'"

# Launch Streamlit with the actual port number - bypass environment variables entirely
echo "=== LAUNCHING STREAMLIT ==="
echo "Command: streamlit run main.py --server.port=$ACTUAL_PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --browser.gatherUsageStats=false"

# Use exec to replace the shell process with Streamlit
# Pass port directly as command line argument to bypass any environment variable issues
exec streamlit run main.py \
    --server.port=$ACTUAL_PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
