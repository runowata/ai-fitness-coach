#!/bin/bash
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Drop all tables completely using raw SQL
echo "Dropping all tables to recreate database from scratch..."
python -c "
import os
import psycopg
from urllib.parse import urlparse

# Parse DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    # Convert postgres:// to postgresql:// for psycopg
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Drop all tables in public schema
            cur.execute(\"\"\"
                DO \$\$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END \$\$;
            \"\"\")
            print('All tables dropped successfully')
" || echo "Could not drop tables, continuing..."

# Run all migrations to create fresh schema
echo "Creating fresh database schema..."
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