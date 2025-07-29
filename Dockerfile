# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including OpenGL libraries
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
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    # X11 libraries for headless operation
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    # Additional graphics support
    libfontconfig1 \
    libfreetype6 \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port that Streamlit runs on (Railway will set PORT dynamically)
EXPOSE 8501

# Health check (Railway handles health checks automatically)
# HEALTHCHECK disabled for Railway compatibility with dynamic ports

# Use shell script entrypoint for proper PORT environment variable expansion
ENTRYPOINT ["/bin/bash"]
CMD ["entrypoint.sh"]
