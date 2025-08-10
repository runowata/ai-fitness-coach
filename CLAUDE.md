# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Fitness Coach

A Django-based web application providing personalized workout programs for gay men, combining fitness training with confidence-building tasks and reward content.

## Tech Stack
- **Backend:** Django 5.0.8, Python 3.12+
- **Database:** PostgreSQL 15+
- **Task Queue:** Celery 5.4.0 + Redis
- **Storage:** AWS S3 + CloudFront CDN / Cloudflare R2 (V2)
- **AI:** OpenAI GPT-4 / Claude (multi-provider via AIClientFactory)
- **Deployment:** Render.com

## Development Commands

### Local Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Load initial data - V2 commands
python manage.py setup_v2_production --data-dir ./data/raw  # Complete V2 setup
# Or individual steps:
python manage.py import_exercises_v2 --data-dir ./data/raw
python manage.py bootstrap_v2_min  # Minimal bootstrap for testing
python manage.py load_weekly_lessons

# Run development server
python manage.py runserver
```

### Running Celery Services
```bash
# Start Redis (required for Celery)
redis-server  # or: docker run -d -p 6379:6379 redis:alpine

# In separate terminals:
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Testing
```bash
pytest                                  # Run all tests
pytest --cov=apps --cov-report=html   # With coverage
pytest -m "not slow"                   # Skip slow tests
pytest tests/test_models.py           # Specific test file
pytest -k test_workout_completion      # Pattern matching
```

### Code Quality
```bash
black . --line-length 100             # Format code
flake8 --max-line-length=100         # Lint
isort . --profile=black               # Sort imports
pre-commit run --all-files            # Run all pre-commit hooks
```

### Database Management
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py migrate <app_name> zero  # Reset app
```

## Architecture Overview

### Apps Structure
- **apps/users/** - Custom User model with timezone/measurement preferences, profiles, gamification
- **apps/workouts/** - Exercise models (CSVExercise), workout plans, daily workouts, video management
- **apps/onboarding/** - Multi-step questionnaire, motivational cards, archetype selection
- **apps/achievements/** - XP system, achievements, progress tracking
- **apps/ai_integration/** - AI service abstraction (AIClientFactory), prompt management (PromptManagerV2)
- **apps/content/** - Media assets (S3/R2), story content system
- **apps/notifications/** - Email notifications via Celery
- **apps/analytics/** - User metrics, workout analytics
- **apps/core/** - Core services including exercise validation, system health monitoring

### Key Models
- `User` → `UserProfile` (1:1) - Custom user with XP, level, stats
- `WorkoutPlan` → `DailyWorkout` → `WorkoutExercise` - AI-generated plans
- `CSVExercise` - V2 exercise model with comprehensive metadata
- `ExplainerVideo` - Exercise video scripts per archetype
- `Achievement` → `UserAchievement` ← `User` - Gamification
- `Story` → `StoryChapter` → `UserStoryAccess` - Content rewards
- `WeeklyLesson` - Weekly motivational content per archetype

### Services (Business Logic)
- `WorkoutPlanGenerator` - AI workout plan creation (apps/ai_integration/services.py)
- `WorkoutCompletionService` - Handles workout completion, XP, achievements (apps/workouts/services.py)
- `VideoPlaylistBuilder` - Assembles video playlists per archetype (apps/workouts/services.py)
- `AchievementChecker` - Checks/awards achievements (apps/achievements/services.py)
- `OnboardingDataProcessor` - Processes onboarding for AI (apps/onboarding/services.py)
- `ExerciseValidationService` - Validates exercise data coverage (apps/core/services/exercise_validation.py)

### AI Integration
- **Prompts:** `prompts/v2/` directory with archetype-specific variations
- **Archetypes:** mentor (Wise Mentor), professional (Pro Coach), peer (Best Mate)
- **Plan Generation:** 4-8 week personalized plans based on onboarding
- **Weekly Adaptation:** Adjusts based on user feedback
- **Multi-provider:** Supports OpenAI and Claude via AIClientFactory

## Key URLs & Endpoints
- `/` - Homepage
- `/users/dashboard/` - Main user dashboard
- `/onboarding/start/` - Start onboarding flow
- `/workouts/daily/<id>/` - Daily workout interface
- `/api/weekly/current/` - Get current week's lesson
- `/api/exercise/{exercise_id}/video/` - Exercise video endpoint
- `/healthz/` - Health check endpoint
- `/admin/` - Django admin panel

## Environment Variables
```bash
SECRET_KEY                  # Django secret (auto-generated in dev)
DATABASE_URL               # PostgreSQL connection
REDIS_URL                  # Redis for Celery (default: redis://localhost:6379)
AWS_ACCESS_KEY_ID          # S3 credentials
AWS_SECRET_ACCESS_KEY      # S3 credentials
OPENAI_API_KEY            # AI service key
EMAIL_HOST_USER           # Email settings
EMAIL_HOST_PASSWORD       # Email settings
CLOUDFRONT_DOMAIN         # CDN domain
R2_* variables            # Cloudflare R2 settings (V2)
BOOTSTRAP_DATA_SHA256     # Bootstrap data integrity check
```

## Media File Structure (V2)
```
# R2/S3 structure:
/videos/exercises/{slug}_technique_{model}.mp4
/videos/exercises/{slug}_mistake_{model}.mp4
/videos/instructions/{slug}_instruction_{archetype}_{model}.mp4
/videos/reminders/{slug}_reminder_{archetype}_{number}.mp4
/videos/motivation/weekly_{archetype}_week{number}.mp4
/images/cards/card_{category}_{number}.jpg
/images/avatars/{archetype}_avatar_{number}.jpg
```

## Important Management Commands

### V2 Production Setup
```bash
# Complete V2 setup (downloads and imports data)
python manage.py setup_v2_production --force-download

# Validation and testing
python manage.py preflight_v2_prod                    # Pre-deployment checks
python manage.py smoke_v2_ready --verbose            # Smoke tests
python manage.py test_ai_generation                  # Test AI generation
python manage.py generate_test_plan_v2 --archetype mentor  # Generate test plan

# Data initialization
python manage.py import_exercises_v2 --data-dir ./data/raw
python manage.py bootstrap_v2_min                    # Minimal bootstrap
python manage.py bootstrap_from_videos               # Legacy bootstrap
python manage.py load_weekly_lessons                 # Load weekly content
python manage.py setup_periodic_tasks                # Setup Celery periodic tasks

# Testing & debugging
python manage.py debug_workout_video <id>            # Debug video system
python manage.py monitor_system_health               # System health check

# Media management
python manage.py import_media /path --dry-run
python manage.py import_media /path --category exercise_technique

# Database cleanup
python manage.py cleanup_legacy_columns              # Remove deprecated columns
```

## Testing Strategy
- Unit tests in `tests/` directory
- Coverage target: ≥80%
- Test fixtures in `fixtures/` for consistent data
- Use `pytest.ini` configuration
- Database reuse enabled for speed (`--reuse-db`)
- Integration tests marked with `@pytest.mark.integration`

## Common Debugging Tools
- Django Debug Toolbar (enabled in DEBUG mode)
- Celery Flower: `celery -A config flower`
- Django shell plus: `python manage.py shell_plus`
- SQL query logging in DEBUG mode
- Management command: `debug_workout_video`
- Health endpoint: `/healthz/`

## Code Style
- **Formatter:** Black (line length 100)
- **Linter:** Flake8 with Django plugin (max line length 100)
- **Import sorting:** isort (profile=black)
- **Pre-commit hooks:** Auto-formatting on commit

## Production Notes
- Platform: Render.com with multi-service setup
- Services: Web (Django), Worker (Celery), Beat (Scheduler)
- Static files: WhiteNoise with compression
- Health monitoring: `/healthz/` endpoint
- Rate limiting: 10 req/min on critical endpoints
- Error tracking: Sentry integration available
- Bootstrap data: Downloaded from GitHub releases or R2