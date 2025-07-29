#!/bin/bash

# Railway-compatible Streamlit entrypoint script
# Handles PORT environment variable expansion properly in Docker

echo "Starting Streamlit application..."

# Get PORT from environment, default to 8501 for local development
PORT=${PORT:-8501}

echo "Using port: $PORT"

# Launch Streamlit with proper environment variable expansion
exec streamlit run main.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
