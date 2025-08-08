# 🚀 V2 Production Deployment Guide

## Pre-Deployment Checklist

### ✅ Code Ready
- [x] Legacy cleanup completed (`chore/cleanup-legacy-archetypes` branch)
- [x] V2 importers created for Excel data
- [x] Database migrations ready (0014, 0015)
- [x] Smoke tests and preflight checks ready

## Render Environment Setup

### 1. Required Environment Variables

Add these in Render Dashboard → Web Service → Environment:

```bash
# R2 Storage (Required)
USE_R2_STORAGE=True
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key  
R2_BUCKET=ai-fitness-media
R2_ENDPOINT=https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com
R2_PUBLIC_BASE=https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev

# OpenAI (Required)
OPENAI_API_KEY=your_openai_key

# Optional but recommended
AWS_QUERYSTRING_EXPIRE=3600
DEBUG=False
```

### 2. Deploy Steps

1. **Merge cleanup branch:**
   ```bash
   git checkout main
   git merge chore/cleanup-legacy-archetypes
   git push origin main
   ```

2. **Wait for Render auto-deploy** or trigger manual deploy

3. **SSH into Render and run setup:**
   ```bash
   python manage.py setup_v2_production --data-dir ./data/raw
   ```

## One-Command Production Setup

The `setup_v2_production` command will:

1. ✅ Apply all database migrations
2. 📊 Import exercises from `base_exercises.xlsx`  
3. 🎥 Import video clips from `explainer_videos_*.xlsx`
4. 🤖 Generate test plans for all archetypes (peer/professional/mentor)
5. 🔍 Run preflight validation checks
6. 🧪 Execute comprehensive smoke tests

### Individual Commands (if needed)

```bash
# Import only
python manage.py import_exercises_v2 --data-dir ./data/raw

# Generate plans only  
python manage.py generate_test_plan_v2 --archetype mentor
python manage.py generate_test_plan_v2 --archetype professional
python manage.py generate_test_plan_v2 --archetype peer

# Validation only
python manage.py preflight_v2_prod
python manage.py smoke_v2_ready --verbose
```

## Expected Results

### Preflight Checks ✅
- No legacy database columns (type, url, technique_video_url, mistake_video_url)
- V2 columns present (r2_kind, archetype)
- No legacy indexes referencing 'type' field
- PROMPTS_PROFILE=v2
- R2 storage configured

### Smoke Test Results ✅
- V2 prompts loaded for all archetypes (peer/professional/mentor)
- Exercise video coverage > 50% (depends on import data)
- Active workout plans present
- Playlist generation working with signed URLs
- Database indexes optimized

## Post-Deployment Validation

### 1. Quick Browser Test
- Visit `/admin/` - login works
- Visit `/` - homepage loads
- Start onboarding flow - archetype selection works
- Generate workout plan - videos play correctly

### 2. CORS Configuration
Apply R2 CORS config from `r2_cors_v2.json`:
```bash
# Upload to R2 bucket settings
rclone copy r2_cors_v2.json r2:ai-fitness-media/cors.json
```

### 3. Monitor Logs
- Check for CORS errors in browser DevTools
- Monitor Render logs for 500 errors
- Verify signed URL generation working

## Rollback Plan (if needed)

If critical issues arise:
1. Revert to previous commit: `git revert HEAD~1 && git push`
2. Database rollback: `python manage.py migrate workouts 0013`
3. Clear R2 CORS: Remove cors configuration from bucket

## Success Criteria

- ✅ Homepage loads without errors
- ✅ Onboarding flow works with new archetypes
- ✅ Video playback functional (no CORS errors)
- ✅ Admin panel accessible 
- ✅ Smoke test passes with minimal warnings
- ✅ No 500 errors in logs for first hour

## Architecture Changes Summary

### Database
- **Removed:** legacy fields (type, url, technique_video_url, mistake_video_url)
- **Added:** r2_kind, r2_file, r2_archetype fields
- **Updated:** archetype choices (peer/professional/mentor)

### Code
- **Replaced:** all bro/sergeant/intellectual → peer/professional/mentor
- **Updated:** templates, views, tests, services
- **Added:** V2 playlist builder with 3-level fallbacks
- **Enhanced:** Exercise validation service with ORM queries

### Storage
- **R2 Integration:** Full CloudFlare R2 with signed URLs
- **CORS Setup:** Browser-compatible video streaming  
- **CDN Ready:** Public URLs for static assets

## Contact & Support

For deployment issues:
1. Check Render logs: Render Dashboard → Logs
2. Run diagnostics: `python manage.py smoke_v2_ready --verbose`
3. Database state: `python manage.py preflight_v2_prod`

Ready to deploy! 🚀