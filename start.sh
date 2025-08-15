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
echo "🌟 Starting gunicorn server with production-ready configuration..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 2 \
  --timeout 600 \
  --graceful-timeout 90 \
  --keep-alive 65 \
  --max-requests 200 --max-requests-jitter 50 \
  --capture-output --log-level info --access-logfile - --error-logfile -
EOF < /dev/null