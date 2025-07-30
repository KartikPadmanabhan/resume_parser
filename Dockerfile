# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including OpenGL libraries
# Group all apt operations together for better caching
RUN apt-get update && apt-get install -y \
    # Core system dependencies
    build-essential \
    pkg-config \
    curl \
    wget \
    # PDF processing dependencies
    poppler-utils \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    # File type detection
    libmagic1 \
    file \
    # OpenGL and graphics libraries (fixes libGL.so.1 error)
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libgl1-mesa-dev \
    libglu1-mesa \
    libglu1-mesa-dev \
    # Additional dependencies for unstructured
    libmagic-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Make startup script executable
RUN chmod +x start.sh

# Switch to appuser
USER appuser

# Expose port (Railway will provide $PORT at runtime)
EXPOSE 8080

# Override Railway's problematic STREAMLIT_SERVER_PORT setting
ENV STREAMLIT_SERVER_PORT=${PORT:-8080}

# Debug: Print health check info during build
RUN echo "🔍 HEALTHCHECK DEBUG: Will use hardcoded 8080 for health check"

# Health check (use hardcoded 8080 like working test branch)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD echo "🔍 HEALTHCHECK DEBUG: Checking health on port 8080" && curl -f http://localhost:8080/_stcore/health || exit 1

# Use startup script with debug and PORT fix
CMD ["./start.sh"]
