# Production Migration Fix - Workouts App

## Problem
- Workouts migrations were marked as `--fake` but tables were never created
- Migration 0008 tries to add field to non-existent `video_clips` table
- Error: `relation "video_clips" does not exist`

## Solution: Clean Reset for Workouts App Only

**Safe because**: No critical user data in workouts tables (users haven't reached video functionality yet)

### Step 1: Access Render Shell
```bash
# In Render dashboard, go to your service -> Shell
python manage.py shell
```

### Step 2: Check Current State  
```bash
# Check migration status
python manage.py showmigrations workouts

# Check migration integrity 
python manage.py check_migration_integrity --app workouts
```

### Step 3: Clean Reset Workouts Tables
```bash
# See what would be dropped (safe preview)
python manage.py drop_workouts_tables --dry-run

# Actually drop workouts tables (THIS REMOVES DATA)
python manage.py drop_workouts_tables --force
```

### Step 4: Reset Migration State
```bash
# Clear fake migration history for workouts
python manage.py migrate workouts zero --fake

# Apply all workouts migrations cleanly
python manage.py migrate workouts --noinput
```

### Step 5: Complete Migration & Setup
```bash
# Apply any remaining migrations
python manage.py migrate --noinput

# Restore workouts data from source
python manage.py setup_v2_production --force-download

# Verify everything works
python manage.py audit_video_clips --summary
python manage.py check_migration_integrity --app workouts
```

## What This Preserves
- ✅ User accounts and profiles 
- ✅ Onboarding data
- ✅ All R2 media files
- ✅ All other app data

## What This Resets
- 🔄 Workout plans (will be regenerated)
- 🔄 Exercise catalog (restored from CSV)
- 🔄 Video clip records (re-synced with R2)

## Future Prevention

The updated `render.yaml` now includes:
- `check_migration_integrity` in pre-deploy to catch this early
- No more `--fake` commands anywhere
- Clean migration path for all deployments

## If Something Goes Wrong

Rollback plan:
1. The old data is gone after step 3, but it wasn't user-critical
2. All source data (exercises, videos) is in R2 and CSV files
3. `setup_v2_production` can restore everything from source
4. Users just need to regenerate their workout plans (normal flow)

## One-Time Execution

**After successful fix**:
1. Delete this file `PRODUCTION_FIX_MIGRATIONS.md`
2. The new migration integrity checks will prevent this issue
3. Future deployments will be clean and safe