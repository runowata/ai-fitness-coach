#!/bin/bash
# Script to setup full environment variables for development

echo "Setting up development environment variables..."

# Django Settings
export DEBUG="True"
export SECRET_KEY="dev-secret-key-12345-not-for-production"
export ALLOWED_HOSTS="localhost,127.0.0.1"

# Database (PostgreSQL local - no SSL)
export DATABASE_URL="postgresql://postgres:@localhost:5432/ai_fitness_coach?sslmode=disable"

# Реальные Cloudflare R2 credentials
export AWS_ACCESS_KEY_ID="3a9fd5a6b38ec994e057e33c1096874e"
export AWS_SECRET_ACCESS_KEY="0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13"
export AWS_S3_ENDPOINT_URL="https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com"
export AWS_STORAGE_BUCKET_NAME="ai-fitness-media"
export R2_PUBLIC_URL="https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
export USE_R2_STORAGE="True"

# AI Integration (Optional for validation)
export OPENAI_API_KEY="sk-test-key-for-validation-only"
export OPENAI_MODEL="gpt-4"

# Redis (for caching)
export REDIS_URL="redis://localhost:6379/0"

# Development flags
export PLAYLIST_STRICT_MODE="False"
export PLAYLIST_FAIL_ON_MISSING_VIDEOS="False"
export STRICT_ACCESS_MIDDLEWARE_ENABLED="False"

echo "✅ All environment variables set successfully!"
echo ""
echo "🔧 Next steps:"
echo "1. Create database: createdb ai_fitness_coach"
echo "2. Run migrations: python manage.py migrate"
echo "3. Load R2 data: python manage.py load_r2_data"
echo "4. Run validation: python manage.py validate_r2_system"