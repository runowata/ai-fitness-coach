# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

AI Fitness Coach - Django-based personalized workout platform for gay men combining fitness training, confidence-building tasks, and gamified content rewards. Features AI-generated workout plans with archetype-based personalization (Mentor/Professional/Peer).

## Tech Stack
- **Backend:** Django 5.0.8, Python 3.12+
- **Database:** PostgreSQL 15+ 
- **Task Queue:** Celery 5.4.0 + Redis
- **Storage:** Cloudflare R2 (primary) / AWS S3 + CloudFront CDN (legacy)
- **AI:** OpenAI GPT-4 / Claude (multi-provider via AIClientFactory)
- **Deployment:** Render.com

## Development Commands

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Load initial data (V2 production setup)
python manage.py setup_v2_production --data-dir ./data/raw
# Or minimal setup for testing:
python manage.py import_exercises_v2 --data-dir ./data/raw
python manage.py bootstrap_v2_min
python manage.py load_weekly_lessons

# Run development server
python manage.py runserver
```

### Running Celery (Background Tasks)
```bash
# Start Redis
redis-server  # or: docker run -d -p 6379:6379 redis:alpine

# In separate terminals:
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test categories (markers defined in pytest.ini)
pytest -m unit                         # Unit tests only
pytest -m integration                  # Integration tests
pytest -m ai                          # AI-related tests
pytest -m "not slow"                   # Skip slow tests
pytest -m e2e                         # End-to-end tests

# Run specific test file or pattern
pytest tests/test_models.py
pytest -k test_workout_completion

# Quick unit tests for CI/CD
DJANGO_SETTINGS_MODULE=config.test_settings pytest -q -k "unit or catalog or whitelist" --tb=short
```

### Code Quality
```bash
black . --line-length 100                                 # Format code
flake8 --max-line-length=100 --ignore=E203,W503         # Lint
isort . --profile=black --line-length=100               # Sort imports
```

## Architecture

### Django Apps Structure
- **users/** - User model, profiles, XP/gamification system
- **workouts/** - Exercise catalog (CSVExercise), workout plans, video management 
- **onboarding/** - Multi-step questionnaire, motivational cards, archetype selection
- **achievements/** - XP system, achievements, progress tracking
- **ai_integration/** - AI service abstraction, prompt management (PromptManagerV2)
- **content/** - Media assets (S3/R2), story content rewards
- **notifications/** - Email notifications via Celery
- **analytics/** - User metrics, workout analytics
- **core/** - System health, exercise validation, middleware

### Key Data Flow
1. **User Registration** → User + UserProfile creation
2. **Onboarding** → Questionnaire → Archetype selection → AI analysis
3. **AI Plan Generation** → OnboardingDataProcessor → WorkoutPlanGenerator → GPT-4/Claude
4. **Daily Workouts** → VideoPlaylistBuilder (archetype-specific videos)
5. **Completion** → WorkoutCompletionService → XP → Achievements
6. **Weekly Adaptation** → Feedback → AI plan adjustment

### Core Services
- `WorkoutPlanGenerator` - AI workout plan creation (apps/ai_integration/services.py)
- `WorkoutCompletionService` - Handles completion, XP, achievements (apps/workouts/services.py)
- `VideoPlaylistBuilder` - Assembles archetype-specific playlists (apps/workouts/services/playlist_v2.py)
- `OnboardingDataProcessor` - Processes onboarding for AI (apps/onboarding/services.py)
- `ExerciseValidationService` - Validates exercise coverage (apps/core/services/exercise_validation.py)

### AI Integration
- **Prompts:** `prompts/v2/` with archetype variations
  - System: `prompts/v2/system/{archetype}.system.md`
  - User: `prompts/v2/user/{archetype}.user.md`
  - Schemas: `prompts/v2/schemas/` for JSON validation
- **Archetypes:** mentor (Wise Mentor), professional (Pro Coach), peer (Best Mate)
- **Providers:** OpenAI GPT-4, Claude (via AIClientFactory)

## Critical Management Commands

### Production Setup & Validation
```bash
# Complete V2 production setup
python manage.py setup_v2_production --force-download

# Pre-deployment validation
python manage.py preflight_v2_prod
python manage.py smoke_v2_ready --verbose
python manage.py monitor_system_health

# Test AI generation
python manage.py test_ai_generation
python manage.py generate_test_plan_v2 --archetype mentor
```

### Data Management
```bash
# Import exercises from CSV
python manage.py import_exercises_v2 --data-dir ./data/raw

# Bootstrap minimal data
python manage.py bootstrap_v2_min

# Load weekly lessons
python manage.py load_weekly_lessons

# Setup Celery periodic tasks
python manage.py setup_periodic_tasks
```

### Video & Media Validation
```bash
# Audit video clips against R2 storage
python manage.py audit_video_clips
python manage.py audit_video_clips --archetype mentor --fail-on-missing

# Sync exercise slugs with video filenames
python manage.py sync_exercise_slugs --dry-run
python manage.py sync_exercise_slugs --fix

# Debug specific workout video issues
python manage.py debug_workout_video <workout_id>
```

### Development Tools (dev_tools/management_commands/)
```bash
# Test AI integration
python manage.py test_gpt5_integration
python manage.py test_comprehensive_ai

# Verify comprehensive flow
python manage.py verify_comprehensive_flow

# Test video playlist generation
python manage.py test_video_playlist
```

## Environment Variables

### Core Settings
```bash
SECRET_KEY                 # Django secret
DATABASE_URL              # PostgreSQL connection
REDIS_URL                 # Redis for Celery
```

### Storage (Cloudflare R2)
```bash
AWS_ACCESS_KEY_ID         # R2 credentials
AWS_SECRET_ACCESS_KEY     # R2 credentials
AWS_STORAGE_BUCKET_NAME   # Bucket name
AWS_S3_ENDPOINT_URL       # R2 endpoint
R2_PUBLIC_URL            # Public URL for media
USE_R2_STORAGE=True      # Enable R2 storage
```

### AI Service
```bash
OPENAI_API_KEY           # OpenAI API key
OPENAI_MODEL             # Model (default: gpt-4)
```

### Strict Mode (Production Validation)
```bash
PLAYLIST_STRICT_MODE=True              # Fail on missing exercises/videos
PLAYLIST_FAIL_ON_MISSING_VIDEOS=True   # Fail on missing R2 files
STRICT_ACCESS_MIDDLEWARE_ENABLED=True  # Protect incomplete user access
```

## R2/S3 Media Structure
```
/videos/exercises/{slug}_technique_{model}.mp4
/videos/exercises/{slug}_mistake_{model}.mp4
/videos/instructions/{slug}_instruction_{archetype}_{model}.mp4
/videos/reminders/{slug}_reminder_{archetype}_{number}.mp4
/videos/motivation/weekly_{archetype}_week{number}.mp4
/images/cards/card_{category}_{number}.jpg
/images/avatars/{archetype}_avatar_{number}.jpg
```

## Key URLs
- `/` - Homepage
- `/users/dashboard/` - User dashboard
- `/onboarding/start/` - Start onboarding
- `/workouts/daily/<id>/` - Daily workout
- `/api/weekly/current/` - Current week's lesson
- `/healthz/` - Health check
- `/admin/` - Django admin

## Deployment (Render.com)

### Configuration
- **render.yaml** - Multi-service configuration (web, worker, beat)
- **Pre-deploy:** Migrations, data import, bootstrap
- **Build:** Install deps, collect static files
- **Start:** Gunicorn with 300s timeout

### Shell Scripts
```bash
./build.sh                     # Build process
./start.sh                     # Start server
./apply_r2_bucket_policy.sh    # Configure R2 CORS
./auto_upload_r2.sh            # Upload media to R2
./reliable_upload.sh           # Upload with retry logic
./monitor_upload.sh            # Monitor upload progress
./deploy_video_fix.sh          # Deploy video fixes
```

## Testing Strategy
- **Framework:** pytest with Django integration
- **Settings:** config.settings_sqlite (test database)
- **Coverage Target:** 80%+
- **Database Reuse:** Enabled for speed (--reuse-db)
- **Markers:** unit, integration, e2e, slow, ai

## Business Logic Notes

### Exercise Fallback System
When exercises unavailable, uses `EXERCISE_FALLBACK_PRIORITY` (apps/workouts/constants.py) to find replacements by muscle groups and equipment.

### Video Playlist Assembly
`VideoPlaylistBuilder` creates personalized sequences:
1. Instruction video (archetype-specific)
2. Technique demonstration
3. Common mistakes
4. Contextual reminders

### XP Calculation
- Base XP: 10-50 points per exercise
- Multipliers: streak bonus, perfect form, time-based
- Level progression: logarithmic

### Archetype Codes
- `111` = Wise Mentor (mentor)
- `112` = Pro Coach (professional)
- `113` = Best Mate (peer)

## Critical Files & Locations
- **Exercise catalog:** apps/workouts/catalog.py
- **AI prompts:** prompts/v2/
- **Video services:** apps/workouts/video_services.py, apps/workouts/services/playlist_v2.py
- **Test fixtures:** fixtures/
- **Raw data:** data/raw/ (Excel files with exercises, videos)
- **Bootstrap data:** Downloaded from GitHub releases or R2