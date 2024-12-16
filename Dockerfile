FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install psycopg2-binary

# Copy application code
COPY server/ .

# Expose port
EXPOSE 8000

# Production command (no reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]