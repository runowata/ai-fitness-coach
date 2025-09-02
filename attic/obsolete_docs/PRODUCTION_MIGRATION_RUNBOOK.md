# Production Migration Runbook

## Overview
This runbook guides the deployment of Django migration fixes to production, specifically addressing the workouts app migration issues that were causing "no such table: csv_exercises" errors on clean installations.

## What Was Fixed
1. **Root Cause**: `apps/workouts/catalog.py` was using non-existent model fields 
2. **Migration Issues**: Conflicting 0002 migrations and unsafe SQL operations
3. **Solution**: Created squashed migration and proper field mapping

## Pre-Deployment Checklist

### 1. Backup Database
```bash
# On Render or production environment
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Verify Repository State
Ensure the following files are present:
- `apps/workouts/migrations/0003_update_csvexercise_r2_structure_squashed_0005_remove_unnecessary_category_field.py` (squashed migration)
- `apps/workouts/migrations/0006_explainervideo_finalvideo_weeklylesson_and_more.py` (new models)
- Fixed `apps/workouts/catalog.py` (uses actual CSVExercise fields)

## Deployment Steps

### Step 1: Apply Squashed Migration
The squashed migration replaces 0003-0005 migrations and will be marked as already applied on production (no actual DDL will run).

```bash
python manage.py migrate workouts --noinput
```

**Expected**: No changes on production database, but migration history is updated.

### Step 2: Apply New Models Migration
Apply the migration that creates new models (ExplainerVideo, WeeklyLesson, etc.).

```bash
# If some tables already exist, use --fake-initial
python manage.py migrate workouts 0006_explainervideo_finalvideo_weeklylesson_and_more --fake-initial --noinput

# If no tables exist, use regular migrate
python manage.py migrate workouts 0006_explainervideo_finalvideo_weeklylesson_and_more --noinput
```

### Step 3: Complete Migration
```bash
python manage.py migrate --noinput
```

### Step 4: Verify Service Health
```bash
# Check that the service starts without errors
python manage.py check

# Test exercise catalog building (this was the main issue)
python manage.py shell -c "from apps.workouts.catalog import ExerciseCatalog; catalog = ExerciseCatalog(); print(f'Loaded {len(catalog.get_exercises())} exercises')"
```

## Troubleshooting

### If Migration 0006 Fails with "VideoClip has no field named 'r2_kind'"
The migration has incorrect operation order. Fix by ensuring all `AddField` operations for VideoClip come before `AlterUniqueTogether` operations.

Temporary workaround:
```bash
# Apply in fake mode first, then real mode
python manage.py migrate workouts 0006_explainervideo_finalvideo_weeslylesson_and_more --fake --noinput
python manage.py migrate workouts 0006_explainervideo_finalvideo_weeklylesson_and_more --noinput
```

### If Tables Already Exist
Use `--fake-initial` flag which safely skips CreateModel operations for existing tables:
```bash
python manage.py migrate workouts 0006_explainervideo_finalvideo_weeklylesson_and_more --fake-initial --noinput
```

### If Unique Constraints Fail
Some indexes or constraints may already exist. Apply specific migration with fake mode:
```bash
python manage.py migrate workouts <migration_number> --fake --noinput
```

## Post-Deployment Validation

### 1. Service Health Check
```bash
curl https://ai-fitness-coach-ttzf.onrender.com/healthz/
```

### 2. Exercise Catalog Test
```bash
python manage.py shell -c "
from apps.workouts.catalog import ExerciseCatalog
catalog = ExerciseCatalog()
exercises = catalog.get_exercises()
print(f'✓ Catalog loaded successfully: {len(exercises)} exercises')
print(f'✓ Sample exercise: {list(exercises.keys())[0] if exercises else \"No exercises\"}')"
```

### 3. AI Workout Generation Test
```bash
python manage.py test_ai_generation --archetype mentor
```

## Environment Variables Check
Ensure these are set in production:
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - Django secret key
- `OPENAI_API_KEY` - AI service key
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` - R2 storage
- `R2_PUBLIC_URL` - R2 CDN endpoint

## CI/CD Updates

### 1. Update GitHub Actions
```yaml
- name: Check migrations are up to date
  env:
    DJANGO_DEBUG: "True"
    DJANGO_SETTINGS_MODULE: "config.settings_sqlite"
  run: |
    python manage.py makemigrations --check --dry-run
```

### 2. Update pytest.ini (if using pytest)
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings_sqlite
```

## Rollback Plan
If issues occur, rollback steps:

1. **Restore Database Backup**:
```bash
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

2. **Revert Code Changes**:
```bash
git revert <commit_hash>
```

3. **Redeploy Previous Version**

## Success Criteria
- ✅ All migrations apply without errors
- ✅ Service starts successfully  
- ✅ Exercise catalog loads without "no such table" errors
- ✅ AI workout generation works
- ✅ No new errors in application logs
- ✅ `makemigrations --check` returns clean on development

## Files Changed
- `apps/workouts/catalog.py` - Fixed field mapping to actual CSVExercise model
- `apps/workouts/migrations/0002_squashed_compat.py` - Converted from squashed to normal
- `apps/workouts/migrations/0003_update_csvexercise_r2_structure_squashed_0005_remove_unnecessary_category_field.py` - New squashed migration
- `apps/workouts/migrations/0006_explainervideo_finalvideo_weeklylesson_and_more.py` - New models migration
- `config/settings_sqlite.py` - SQLite settings for local development
- `.gitignore` - Added dev.sqlite3

## Contact
For issues during deployment, check:
1. Application logs in Render dashboard
2. Database connection status
3. Environment variables configuration

---
**Created**: 2025-08-25  
**Last Updated**: 2025-08-25  
**Migration Chain**: 0001 → 0002_squashed_compat → 0006_merge → 0003_squashed_0005 → 0006_new_models