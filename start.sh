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
echo "🌟 Starting gunicorn server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 300
EOF < /dev/null