#!/bin/bash
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Migrations moved to Pre-Deploy Command
echo "Skipping migrations (handled by Pre-Deploy)..."

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

# Fixtures loading removed (obsolete)
echo "Skipping fixtures (data comes from bootstrap)..."

# Bootstrap video data on deployment
echo "Bootstrapping video data..."
python manage.py bootstrap_from_videos --media-path=/opt/render/project/src/media --force || \
  echo "⚠️  Bootstrap skipped. Media not mounted."

echo "Build completed successfully!"