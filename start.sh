#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Loading fixtures..."
python manage.py loaddata fixtures/exercises.json
python manage.py loaddata fixtures/onboarding_questions.json
python manage.py loaddata fixtures/motivational_cards.json
python manage.py loaddata fixtures/stories.json
python manage.py loaddata fixtures/video_clips.json
python manage.py loaddata fixtures/achievements.json

echo "Starting gunicorn on port $PORT..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 300 --log-file -