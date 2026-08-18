FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements.txt .

# Install dependencies (includes both backend and AI packages)
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (includes the merged AI package at app/ai/)
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/drafts

# Expose the API port
EXPOSE 8000

# Run migrations and start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

