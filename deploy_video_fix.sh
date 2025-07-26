#!/bin/bash
# Deployment script to fix video issues on Render

echo "=== Fixing Video System on Production ==="

# 1. Run migrations
echo "Running migrations..."
python manage.py migrate

# 2. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 3. Fix video URLs in database
echo "Fixing video URLs..."
python fix_video_urls.py

# 4. Run video system debug
echo "Running video system debug..."
python debug_video_system.py

# 5. Check specific workout if provided
if [ ! -z "$1" ]; then
    echo "Checking workout $1..."
    python debug_video_system.py $1
fi

echo "=== Video fix complete ==="