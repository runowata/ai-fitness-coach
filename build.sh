#!/bin/bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Load fixtures
python manage.py loaddata fixtures/exercises.json
python manage.py loaddata fixtures/onboarding_questions.json
python manage.py loaddata fixtures/motivational_cards.json
python manage.py loaddata fixtures/stories.json
python manage.py loaddata fixtures/video_clips.json
python manage.py loaddata fixtures/achievements.json

echo "Build completed successfully!"