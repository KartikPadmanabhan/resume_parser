#!/bin/bash

# Startup script for Railway deployment
# Detects Railway environment and uses PORT variable only when needed

# Check if we're running on Railway (Railway sets RAILWAY_ENVIRONMENT)
if [ -n "$RAILWAY_ENVIRONMENT" ] && [ -n "$PORT" ]; then
    echo "Starting Streamlit app on Railway with port $PORT"
    # Railway deployment - use PORT variable
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
