FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for layer caching)
COPY requirements.txt .

# Install backend dependencies, including the AI package from parent directory
# Note: The AI package path in -e ../app is relative to /app, which maps to backend/
# The docker-compose mounts the AI package at /app/../app
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/drafts

# Expose the API port
EXPOSE 8000

# Run migrations and start the server
# (This will be overridden by docker-compose command for development)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

