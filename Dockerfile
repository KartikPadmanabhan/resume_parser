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

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint script executable and ensure proper line endings
RUN chmod +x entrypoint.sh && \
    dos2unix entrypoint.sh 2>/dev/null || true

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (Railway will override this)
EXPOSE 8501

# Add healthcheck for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Use the entrypoint script for proper debugging and PORT handling
ENTRYPOINT ["./entrypoint.sh"]
