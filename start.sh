#\!/bin/bash
set -e

echo "🚀 Starting AI Fitness Coach deployment..."

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Setup database with bootstrap
echo "🏗️ Setting up database..."
python manage.py setup_database

# Start gunicorn
echo "🌟 Starting gunicorn server with extended timeout for AI operations..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 600 --keep-alive 65
EOF < /dev/null