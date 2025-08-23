#!/bin/bash

# Script to fix migration conflicts during deployment
echo "🔧 Fixing migration conflicts..."

# Rollback onboarding migrations to clean state
echo "Rolling back onboarding migrations..."
python manage.py migrate onboarding 0001 --noinput

# Apply all migrations normally
echo "Applying all migrations..."
python manage.py migrate --noinput

echo "✅ Migration fix completed!"