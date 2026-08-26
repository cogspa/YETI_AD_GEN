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

# Set default port for Cloud Run (defaults to 8080)
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
