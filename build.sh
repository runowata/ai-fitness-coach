#!/bin/bash
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate --verbosity=2

# Debug: Check static files structure
echo "Checking static files..."
ls -la static/ || echo "No static directory found"
ls -la static/css/ || echo "No CSS directory found"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --verbosity=2

# Debug: Check collected files
echo "Checking collected static files..."
ls -la staticfiles/ || echo "No staticfiles directory found"
ls -la staticfiles/css/ || echo "No CSS files collected"

# Load fixtures - Keep only empty.json to prevent build failure
echo "Loading minimal fixtures..."
python manage.py loaddata fixtures/empty.json

# Bootstrap video data on deployment
echo "Bootstrapping video data..."
python manage.py bootstrap_from_videos --force || \
  echo "⚠️  Bootstrap skipped. Media not mounted."

echo "Build completed successfully!"