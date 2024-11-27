#!/bin/bash

mkdir -p ./certbot/www
mkdir -p ./certbot/conf

# Start with init config
ENVIRONMENT=init docker compose up --force-recreate -d nginx

# Get initial certificate
docker compose run --rm certbot \
  certonly --webroot \
  --webroot-path=/var/www/html \
  --email ${SSL_EMAIL} \
  --agree-tos \
  --no-eff-email \
  -d fitboks.projekts.tech

# Restart with prod config
docker compose down
ENVIRONMENT=prod docker compose --profile prod up -d