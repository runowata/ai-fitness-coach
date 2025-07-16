# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
AI Fitness Coach is a Django web application for personalized fitness training specifically designed for gay men. It combines fitness workouts with confidence-building tasks and gamified progression through an XP/achievement system.

## Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

### Running the Application
```bash
python manage.py runserver
```

### Testing
```bash
pytest                           # Run all tests
pytest tests/test_models.py      # Run specific test file
pytest -m "not slow"            # Skip slow tests
pytest -k "test_user"           # Run tests matching pattern
```

### Database Operations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata fixtures/*.json
```

### Custom Management Commands
```bash
python manage.py populate_video_clips --dry-run
python manage.py populate_video_clips --video-path=static/videos
python manage.py import_media /path/to/media --category exercise_technique
```

## Architecture Overview

### Core Django Apps Structure
- **users**: Custom user model (AbstractUser) with profiles, 2FA, XP system
- **workouts**: Exercise database, workout plans, video management, playlist building  
- **onboarding**: Multi-step questionnaire for personalized plan generation
- **content**: Story/chapter system for gamified rewards
- **achievements**: XP/level system with unlockable content
- **ai_integration**: OpenAI/Claude integration for workout plan generation
- **core**: Basic views and utilities

### Key Models Relationships
```
User (AbstractUser)
├── completed_onboarding (BooleanField) - simple onboarding status check
├── UserProfile (1:1) - XP, archetype, preferences  
├── WorkoutPlan (1:N) - AI-generated fitness plans
├── UserOnboardingResponse (1:N) - questionnaire data
└── UserAchievement (1:N) - unlocked achievements

Exercise (varchar primary key)
├── VideoClip (1:N) - technique, mistake, instruction videos
└── DailyWorkout.exercises (JSON field) - workout compositions

WorkoutPlan  
└── DailyWorkout (1:N) - individual workout sessions
```

### Critical Database Notes
- **Exercise.id**: Uses CharField(max_length=36) instead of standard BigAutoField to match existing database
- **User model**: Custom table name 'users', email as USERNAME_FIELD
- **VideoClip vs MediaAsset**: Dual video management systems exist - VideoClip is the active one used by VideoPlaylistBuilder

### AI Integration Architecture
1. **Onboarding Collection**: Multi-step form captures user preferences
2. **Plan Generation**: Uses prompts/workout_plan_generation.txt with OpenAI/Claude
3. **Weekly Adaptation**: Adjusts plans based on user feedback via prompts/weekly_adaptation.txt
4. **Data Flow**: UserOnboardingResponse → AI prompt → WorkoutPlan JSON → DailyWorkout records

### Video System Architecture
- **Storage**: Static files in development, Render persistent disk (10GB) in production
- **Organization**: `/videos/exercises/{slug}_{type}_{model}.mp4`, `/videos/trainers/{archetype}_{type}.mp4`
- **Playlist Building**: VideoPlaylistBuilder service constructs workout video sequences
- **Types**: technique, mistake, instruction, reminder, weekly, final

### Onboarding Flow
1. User registers → redirected to onboarding:start
2. User completes questionnaire → OnboardingDataService.mark_onboarding_complete()
3. Sets User.completed_onboarding = True (prevents redirect loops)
4. User redirected to dashboard with active workout plan

### Gamification Flow
1. User completes workout → WorkoutCompletionService
2. XP awarded (50-125 points) → UserProfile.add_xp()
3. Achievement check → AchievementChecker.check_achievements()
4. Story access unlocked → UserStoryAccess records
5. Level progression (100 XP = 1 level)

## Development Patterns

### Model Field Compatibility
When modifying models, check existing database constraints:
- Exercise uses CharField primary key (varchar(36))
- User table may have missing AbstractUser fields - use migration 0002_add_missing_user_fields.py

### Video File Management  
- Videos excluded from Git (.gitignore: static/videos/, *.mp4)
- Use populate_video_clips command to sync filesystem with VideoClip records
- VideoPlaylistBuilder expects specific naming convention: {exercise_slug}_{type}_{archetype}_{model}.mp4

### AI Prompt Integration
- Templates in prompts/ directory use {variable} substitution
- AI responses expected as JSON with specific structure
- Error handling for malformed AI responses in ai_integration/services.py

### Environment Configuration
- Development: DEBUG=True, local database, static files
- Production (Render): RENDER=1 env var, persistent disk for media, PostgreSQL

## Common Issues

### Database Schema Mismatches
- Run migration 0002_add_missing_user_fields.py if "password column does not exist" error occurs
- Exercise model uses non-standard primary key - maintain CharField(max_length=36)

### Video Management
- VideoClip table empty after media upload: run `python manage.py populate_video_clips`
- Missing videos in playlists: check file naming convention matches VideoPlaylistBuilder expectations

### Deployment (Render.com)
- Update render.yaml startCommand from Flask to Django: `gunicorn config.wsgi:application`
- Ensure RENDER environment variable set for production settings
- Run migrations after deployment: `python manage.py migrate`

## Testing Strategy
- Unit tests in tests/ directory
- Pytest configuration in pytest.ini with Django settings
- Markers available: `slow` for performance tests
- Coverage target: ≥80%

## Security Notes
- Custom user model with email authentication
- 2FA support via django-otp
- Adult content verification (is_adult_confirmed field)
- Age verification minimum 18 years (settings.MINIMUM_AGE)