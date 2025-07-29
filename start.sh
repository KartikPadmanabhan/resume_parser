#!/bin/bash

# Startup script for Railway deployment
# Uses PORT variable if it's set and valid, otherwise defaults to 8501

# Check if PORT is set and is a valid number
if [ -n "$PORT" ] && [ "$PORT" -eq "$PORT" ] 2>/dev/null; then
    echo "Starting Streamlit app with port $PORT"
    # Use PORT variable (Railway or custom)
    exec streamlit run main.py \
        --server.port=$PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=false \
        --server.enableXsrfProtection=false
else
    echo "Starting Streamlit app locally on port 8501"
    # Local development - use default port 8501
    exec streamlit run main.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=false \
        --server.enableXsrfProtection=false
fi
