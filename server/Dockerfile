# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait-for-db script
COPY start.sh .
RUN chmod +x start.sh

# Copy the rest of the application
COPY . .

# Expose port 3000
EXPOSE 3000

# Command to run the application with wait-for-db script
CMD ["./start.sh"]