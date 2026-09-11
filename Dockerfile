# ==============================================================================
# GOOGLE CLOUD RUN CONFIGURATION
# ==============================================================================
# This Dockerfile packages the FastAPI backend for deployment to Google Cloud Run:
# Service: yeti-ad-backend (us-central1)
# Production URL: https://yeti-ad-backend-545916247776.us-central1.run.app
# Cloud Run injects the $PORT environment variable (default 8080) and routes traffic.
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# GOOGLE CLOUD RUN ENVIRONMENT:
# Cloud Run automatically sets the PORT environment variable (default 8080).
# The service listens on 0.0.0.0 to receive incoming container requests.
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app

EXPOSE 8080

# Launch Uvicorn server bound to Google Cloud Run port
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]

