#!/bin/bash

# Exit on error
set -e

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Load environment variables
source .env

# Verify required variables
if [ -z "$SSL_EMAIL" ]; then
    echo "Error: SSL_EMAIL not set in .env"
    exit 1
fi

mkdir -p ./certbot/www
mkdir -p ./certbot/conf

# Start with init config
echo "Starting nginx..."
ENVIRONMENT=init docker compose up --force-recreate -d nginx

# Get initial certificate (with staging flag for testing)
echo "Requesting certificate..."
docker compose run --rm certbot \
  certonly --webroot \
  --webroot-path=/var/www/html \
  --email $SSL_EMAIL \
  --agree-tos \
  --no-eff-email \
  --staging \
  -d fitboks.projekts.tech

# Restart with prod config
echo "Restarting in prod mode..."
docker compose down
ENVIRONMENT=prod docker compose --profile prod up -d

echo "Setup complete! Check certificates and remove --staging flag if successful"