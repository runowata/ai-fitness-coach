#!/bin/bash
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
# Mark migration 0003 as already applied since fields don't exist in production
python manage.py migrate workouts 0002 --fake
python manage.py migrate workouts 0003 --fake
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

# Load fixtures
python manage.py loaddata fixtures/exercises.json
python manage.py loaddata fixtures/onboarding_questions.json
python manage.py loaddata fixtures/motivational_cards.json
python manage.py loaddata fixtures/stories.json
python manage.py loaddata fixtures/achievements.json

echo "Build completed successfully!"