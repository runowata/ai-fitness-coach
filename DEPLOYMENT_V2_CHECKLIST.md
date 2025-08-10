# 🚀 V2 Clean Cut Deployment Checklist

## Pre-deployment (Local)

### 1. Code Verification
- [x] All v1 artifacts removed (prompts/*.txt files deleted)
- [x] Legacy fields removed from models (technique_video_url, mistake_video_url, url, type)
- [x] PROMPTS_PROFILE hardcoded to 'v2'
- [x] Archetype values updated (peer/professional/mentor only)
- [x] Admin interface updated for new fields

### 2. Tests
```bash
# Run all tests
pytest tests/test_media_service.py tests/test_prompt_manager.py -v
pytest tests/test_playlist_v2.py tests/test_schema_workout_plan.py -v

# Run smoke test
python manage.py smoke_v2_ready --verbose
```

### 3. Migrations Ready
```bash
# Check migration plan
python manage.py migrate --plan

# Expected:
# - users.0007_update_archetype_choices_v2
# - workouts.0014_clean_v1_legacy
```

## Deployment Steps

### 1. Pre-deployment Backup
```bash
# Backup database (on Render/production)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Environment Variables
Verify on Render.com:
- `USE_R2_STORAGE=True`
- `R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com`
- `R2_ACCESS_KEY_ID=xxx`
- `R2_SECRET_ACCESS_KEY=xxx`
- `R2_BUCKET=ai-fitness-media`
- `R2_PUBLIC_BASE=https://pub-xxx.r2.dev` (if using public CDN)
- `AWS_QUERYSTRING_EXPIRE=7200`
- `OPENAI_API_KEY=xxx`
- Remove `PROMPTS_PROFILE` (hardcoded now)

### 3. Deploy Code
```bash
# Push to main branch
git add -A
git commit -m "🚀 Deploy clean v2: removed legacy, unified archetypes"
git push origin main
```

### 4. Run Migrations
```bash
# On Render shell or via SSH
python manage.py migrate

# Create new indexes for playlist queries
python manage.py makemigrations --name add_v2_indexes
python manage.py migrate
```

### 5. Configure R2 CORS
```bash
# Apply CORS configuration to R2 bucket
aws s3api put-bucket-cors \
  --bucket ai-fitness-media \
  --cors-configuration file://r2_cors_v2.json \
  --endpoint-url $R2_ENDPOINT \
  --profile r2
```

### 6. Verify Content Types
```bash
# Check and fix Content-Type metadata
python scripts/check_r2_content_types.py --bucket ai-fitness-media --fix
```

### 7. Post-deployment Verification
```bash
# Run smoke test on production
python manage.py smoke_v2_ready --verbose

# Check coverage
python manage.py shell
>>> from apps.core.services.exercise_validation import ExerciseValidationService
>>> service = ExerciseValidationService()
>>> report = service.get_coverage_report()
>>> print(f"Coverage: {report['coverage_percentage']}%")
```

### 8. Test User Flow
1. Create test user account
2. Complete onboarding with archetype selection (peer/professional/mentor)
3. Verify workout plan generated
4. Open daily workout
5. Check:
   - Videos load and play
   - Poster images display
   - No CORS errors in console
   - Signed URLs work

## Rollback Plan

If issues occur:
```bash
# Revert migrations
python manage.py migrate workouts 0013
python manage.py migrate users 0006

# Restore from backup
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql

# Revert code
git revert HEAD
git push origin main
```

## Success Criteria

✅ All checks must pass:
- [ ] smoke_v2_ready shows no errors
- [ ] >10% exercise coverage with videos
- [ ] Test user can complete onboarding
- [ ] Workout videos play without errors
- [ ] No 500 errors in logs
- [ ] Response times <2s for playlist generation

## Monitoring

Watch for 24h after deployment:
- Sentry/error tracking for exceptions
- Server logs for 500 errors
- User feedback for video playback issues
- Database query performance (indexes working)

## Notes

- R2 file field remains nullable until 100% coverage
- Archetype fallback logic ensures videos always found
- Cache TTL set to 5min for signed URLs (configurable)
- Weekly adaptation still uses same AI endpoint