# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Fitness Coach

A Django-based web application providing personalized workout programs for gay men, combining fitness training with confidence-building tasks and reward content. The app features AI-generated workout plans, gamification, and personalized content based on user archetype selection.

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

# Run specific test categories (from pytest.ini markers)
pytest -m unit                         # Unit tests only
pytest -m integration                  # Integration tests
pytest -m ai                          # AI-related tests
DJANGO_SETTINGS_MODULE=config.test_settings pytest -q -k "unit or catalog or whitelist" --tb=short
```

### Code Quality
```bash
black . --line-length 100             # Format code
flake8 --max-line-length=100 --ignore=E203,W503  # Lint
isort . --profile=black --line-length=100  # Sort imports
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

### Data Flow
1. **User Registration** → Creates User + UserProfile with default settings
2. **Onboarding Flow** → Collects user data, shows motivational cards, archetype selection
3. **AI Plan Generation** → OnboardingDataProcessor → WorkoutPlanGenerator → AI (GPT-4/Claude)
4. **Daily Workouts** → VideoPlaylistBuilder assembles videos based on archetype
5. **Workout Completion** → WorkoutCompletionService → XP calculation → Achievement checking
6. **Weekly Adaptation** → Collects feedback → AI adjusts next week's plan

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
  - System prompts: `prompts/v2/system/{archetype}.system.md`
  - User prompts: `prompts/v2/user/{archetype}.user.md`
  - Schemas: `prompts/v2/schemas/` for JSON response validation
- **Archetypes:** 
  - `mentor` (Wise Mentor) - Supportive, experienced guide
  - `professional` (Pro Coach) - Direct, no-nonsense trainer
  - `peer` (Best Mate) - Friendly workout buddy
- **Plan Generation:** 4-8 week personalized plans based on onboarding
- **Weekly Adaptation:** Adjusts based on user feedback
- **Multi-provider:** Supports OpenAI and Claude via AIClientFactory
- **Comprehensive Analysis:** Deep AI assessment of user profile for better personalization

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

# AWS S3 / Cloudflare R2
AWS_ACCESS_KEY_ID          # S3/R2 credentials
AWS_SECRET_ACCESS_KEY      # S3/R2 credentials
AWS_STORAGE_BUCKET_NAME    # Bucket name
AWS_S3_ENDPOINT_URL        # R2 endpoint (for R2)
R2_PUBLIC_URL              # R2 public URL

# AI Service
OPENAI_API_KEY            # OpenAI API key
OPENAI_MODEL              # Model (default: gpt-4)

# Email
EMAIL_HOST_USER           # Email settings
EMAIL_HOST_PASSWORD       # Email settings

# Media
CLOUDFRONT_DOMAIN         # CDN domain
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
- Slow tests marked with `@pytest.mark.slow`
- AI tests marked with `@pytest.mark.ai`

## Common Debugging Tools
- Django Debug Toolbar (enabled in DEBUG mode)
- Celery Flower: `celery -A config flower`
- Django shell plus: `python manage.py shell_plus`
- SQL query logging in DEBUG mode
- Management command: `debug_workout_video`
- Health endpoint: `/healthz/`

## Code Style
- **Formatter:** Black (line length 100)
- **Linter:** Flake8 (max line length 100, ignore E203,W503)
- **Import sorting:** isort (profile=black, line length 100)
- **Security:** Bandit for security issues
- **Django:** django-upgrade for Django 5.0 compatibility
- **Pre-commit hooks:** Auto-formatting and tests on commit

## Production Notes
- Platform: Render.com with multi-service setup
- Services: Web (Django), Worker (Celery), Beat (Scheduler)
- Static files: WhiteNoise with compression
- Health monitoring: `/healthz/` endpoint
- Rate limiting: 10 req/min on critical endpoints
- Error tracking: Sentry integration available
- Bootstrap data: Downloaded from GitHub releases or R2
- Data integrity: SHA256 check via BOOTSTRAP_DATA_SHA256 env var

## Critical Business Logic

### Exercise Fallback System
When an exercise is unavailable, the system uses `EXERCISE_FALLBACK_PRIORITY` (apps/workouts/constants.py) to find replacements based on muscle groups and equipment availability.

### Video Playlist Assembly
The `VideoPlaylistBuilder` (apps/workouts/services/playlist_v2.py) creates personalized video sequences:
1. Instruction video (archetype-specific)
2. Technique demonstration
3. Common mistakes
4. Contextual reminders

### XP Calculation
- Base XP per exercise: 10-50 points based on difficulty
- Multipliers: streak bonus, perfect form, time-based
- Level thresholds: logarithmic progression

### Archetype Codes
- `111` = Wise Mentor (mentor)
- `112` = Pro Coach (professional)  
- `113` = Best Mate (peer)

## Troubleshooting

### Common Issues
1. **Media not loading**: Check R2_PUBLIC_URL and AWS credentials
2. **AI generation failing**: Verify OPENAI_API_KEY and check prompts/v2/ files
3. **Celery tasks not running**: Ensure Redis is running and REDIS_URL is correct
4. **Migration issues**: Run `python manage.py migrate --run-syncdb`

### Debug Commands
```bash
# Check system health
python manage.py monitor_system_health

# Debug specific workout video issues
python manage.py debug_workout_video <workout_id>

# Verify exercise data coverage
python manage.py preflight_v2_prod

# Test AI generation without creating real data
python manage.py test_ai_generation

# Analyze video playlist structure
python manage.py playlist_analysis_deep
```