# Code Review Copy for GPT Analysis

## Location
This project copy is located at: `/Users/alexbel/Desktop/Проекты/AI Fitness Coach - Code Review/`

## What's Included
✅ All source code files (.py, .html, .js, .css, .yaml, .json, .md)
✅ Django apps structure and migrations  
✅ Configuration files (settings, requirements, etc.)
✅ Templates and static files
✅ Documentation and deployment guides
✅ Test files and fixtures

## What's Excluded (for GPT upload)
❌ Virtual environment (.venv, venv, env)
❌ Python cache files (__pycache__, *.pyc)
❌ Git repository (.git)
❌ Node modules (node_modules)
❌ Local database (db.sqlite3)
❌ Redis dump (dump.rdb)
❌ Static files collection (staticfiles)

## Recent Changes (Latest Commit)
**feat: migrate MotivationalCard to path-based R2 URLs**

Key changes made:
- Added `path` field to MotivationalCard model for relative R2 paths
- Created migrations to add and populate path field from existing image_url data
- Added utility functions in `apps/onboarding/utils.py` for R2 URL handling
- Updated views and model properties to prioritize path field over absolute URLs
- Created management commands for safe migration with dry-run support
- Maintained backward compatibility during transition period

**Result**: Future R2 domain changes now require only R2_PUBLIC_BASE environment variable update, no more database mass updates needed.

## Directory Structure
```
AI Fitness Coach - Code Review/
├── apps/                    # Django applications
│   ├── onboarding/         # User onboarding with motivational cards
│   ├── workouts/           # Exercise and workout management
│   ├── users/              # User profiles and authentication
│   ├── achievements/       # XP system and gamification
│   ├── ai_integration/     # AI service integration (GPT-4/Claude)
│   └── ...
├── config/                 # Django settings and configuration
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── tests/                  # Test suite
├── prompts/v2/             # AI prompts for different archetypes
├── requirements.txt        # Python dependencies
├── CLAUDE.md              # Development documentation
└── README.md              # Project overview
```

## Architecture Highlights
- **Tech Stack**: Django 5.0.8, PostgreSQL, Redis, Celery, AWS S3/Cloudflare R2
- **AI Integration**: Multi-provider support (OpenAI GPT-4, Claude) with archetype-specific prompts
- **Storage**: Cloudflare R2 with CDN for media assets
- **Deployment**: Render.com with multi-service setup

## Size: ~74MB
Perfect for GPT-4 analysis and code review.