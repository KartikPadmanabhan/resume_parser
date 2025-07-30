# Minimal Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Debug: Print environment info during build
RUN echo "🔍 BUILD DEBUG: Container environment setup complete"

# Expose port
EXPOSE 8080

# Override Railway's problematic STREAMLIT_SERVER_PORT setting
ENV STREAMLIT_SERVER_PORT=${PORT:-8501}

# Debug: Print startup info
RUN echo "🔍 STARTUP DEBUG: Dockerfile will use start.sh script"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Use startup script with debug
CMD ["./start.sh"]
