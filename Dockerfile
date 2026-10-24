# Production Dockerfile for Natura Siberica Enterprise Agents
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY config/ ./config/
COPY agents/ ./agents/
COPY data/ ./data/
COPY tests/ ./tests/
COPY app.py .

# Environment
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI Gateway
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
