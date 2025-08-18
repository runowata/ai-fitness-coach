#!/bin/bash
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Completely drop and recreate all tables
echo "Dropping all database tables..."
python -c "
import os
import psycopg

# Parse DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    # Convert postgres:// to postgresql:// for psycopg
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Drop all tables in public schema
                cur.execute('''
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                ''')
                tables = cur.fetchall()
                
                for table in tables:
                    cur.execute(f'DROP TABLE IF EXISTS \"{table[0]}\" CASCADE')
                    print(f'Dropped table: {table[0]}')
                
                # Reset django_migrations table
                cur.execute('CREATE TABLE IF NOT EXISTS django_migrations (id SERIAL PRIMARY KEY, app VARCHAR(255), name VARCHAR(255), applied TIMESTAMP)')
                cur.execute('DELETE FROM django_migrations')
                print('Cleared migration history')
    except Exception as e:
        print(f'Database reset error: {e}')
        print('Continuing with migrations...')
"

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