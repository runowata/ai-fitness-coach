# Changelog

All notable changes to AI Fitness Coach will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0-rc1] - 2025-08-06

### Added

#### Backend API Enhancements
- **NEW:** `/api/weekly/unread/` endpoint - returns `{"unread": true/false}` for frontend notification indicators
- **NEW:** `duration_sec` field in WeeklyLesson model and serializer for lesson duration display
- **NEW:** Database-agnostic safe migration system for production deployments
- **NEW:** Redis health check in `/healthz/` monitoring endpoint

#### Weekly Lesson System (Complete 8-Week Program)
- **NEW:** WeeklyNotification model for frontend-consumed lesson delivery
- **NEW:** `enqueue_weekly_lesson` Celery task (replaces email sending with DB records)
- **NEW:** Complete YAML content for weeks 1-8 with 3 archetype variants each
- **NEW:** `load_weekly_lessons` management command for YAML content import
- **NEW:** Automated content loading during deployment

#### Infrastructure & DevOps
- **NEW:** Production-ready Celery + Redis setup in render.yaml
- **NEW:** Celery beat scheduler for automated weekly lesson delivery
- **NEW:** Comprehensive monitoring and health checks
- **NEW:** Database-agnostic migration system (SQLite dev + PostgreSQL prod)

### Changed

#### Backend Improvements
- **IMPROVED:** Archetype system fully unified with numeric codes (111/222/333)
- **IMPROVED:** All API endpoints now use proper Django REST Framework patterns
- **IMPROVED:** Migration system handles existing database schemas safely
- **IMPROVED:** Comprehensive test coverage for all weekly lesson endpoints

#### Content Management
- **IMPROVED:** Weekly lessons now managed via version-controlled YAML files
- **IMPROVED:** Content loading integrated into deployment pipeline
- **IMPROVED:** Support for multiple locales and archetypes per lesson

### Fixed

#### Critical Production Issues
- **FIXED:** Migration conflicts blocking production deployments
- **FIXED:** Equipment column duplication error in production database
- **FIXED:** Timezone import errors in Celery tasks
- **FIXED:** Test suite compatibility with unified archetype system

### Technical Details

#### API Endpoints
```
GET /api/weekly/current/     - Get current unread lesson (marks as read)
GET /api/weekly/unread/      - Check if user has unread lessons
GET /api/weekly/<int:week>/  - Get specific lesson by week number
GET /api/archetype/          - Update user archetype preference
GET /api/exercise/<id>/video/ - Get exercise explainer video
GET /healthz/                - System health check (now includes Redis)
```

#### Database Schema
- WeeklyNotification model: user notifications for lessons
- WeeklyLesson model: lesson content with duration tracking
- FinalVideo model: completion video content
- Safe migration system for production compatibility

#### Infrastructure
- Redis: Message broker for Celery
- Celery Worker: Background task processing
- Celery Beat: Scheduled task execution (weekly lessons)
- Health monitoring: Database + Redis + AI API checks

### Migration Guide

#### From Previous Versions
1. Run migrations: `python manage.py migrate`
2. Load lesson content: `python manage.py load_weekly_lessons`
3. Verify health: `curl /healthz/`

#### Breaking Changes
- Archetype values changed from strings to numeric codes
- Weekly lesson delivery switched from email to API-based system
- Old weekly lesson email templates no longer used

## [Previous Versions]

### [0.8.0] - Sprint 3 Completion
- Basic weekly lesson email system
- Initial archetype implementation
- Core workout and user management features

### [0.7.0] and earlier
- Core application functionality
- User authentication and profiles
- Exercise and workout management
- Achievement system