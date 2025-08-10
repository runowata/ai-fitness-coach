# 🚀 Render Deployment Guide

## Quick Deploy Steps

### 1. Commit & Push
```bash
git checkout -b release/ready-for-render
git add .
git commit -m "release: production deploy (R2, AI whitelist, deterministic playlists, CI)

- Multi-provider video storage with R2/CDN support
- Strict AI exercise validation with whitelist enforcement  
- Deterministic playlist generation with multi-level fallbacks
- Comprehensive test coverage with GitHub Actions CI
- Production health monitoring and deployment scripts"

git push -u origin release/ready-for-render
```

### 2. Render Environment Variables

#### R2 Storage Configuration
```
AWS_ACCESS_KEY_ID=your-r2-access-key
AWS_SECRET_ACCESS_KEY=your-r2-secret-key  
AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=ai-fitness-media
```

#### Video & AI Features
```
R2_SIGNED_URLS=true
R2_SIGNED_URL_TTL=3600
R2_CDN_BASE_URL=
SHOW_AI_ANALYSIS=true
AI_REPROMPT_MAX_ATTEMPTS=2
PLAYLIST_MISTAKE_PROB=0.30
FALLBACK_TO_LEGACY_FLOW=false
```

#### AI Services
```
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...  # if using Claude
```

#### Database & Cache (Auto-configured by Render)
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...  # if using Redis addon
```

### 3. Render Build Configuration

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn config.wsgi:application
```

**Post-Deploy Command (Optional):**
```bash
python manage.py migrate
```

### 4. Post-Deploy Setup

#### One-time Data Backfill
```bash
# Set provider field for existing R2 clips
python manage.py shell -c "
from apps.workouts.models import VideoClip
count = VideoClip.objects.filter(r2_file__isnull=False).update(provider='r2')
print(f'Updated {count} clips with provider=r2')
"
```

#### Production Health Check
```bash
python scripts/production_health_check.py
```

Expected output:
```
🚀 Production Health Check
Environment: ✅ PASS
Database: ✅ PASS  
Video Storage: ✅ PASS
AI Whitelist: ✅ PASS
AI Generator: ✅ PASS

🎉 System ready for production!
```

### 5. Smoke Test Checklist

- [ ] **Home page** loads successfully
- [ ] **Onboarding flow**:
  - [ ] Analysis preview shows
  - [ ] Plan confirmation works
  - [ ] First workout opens
- [ ] **Video playlist**:
  - [ ] Intro/technique/instruction videos load
  - [ ] All URLs return 200 status
  - [ ] Rest day shows weekly/closing content
- [ ] **Metrics in logs**:
  - [ ] `ai.whitelist.exercises_count`
  - [ ] `video.playlist.build_time_ms`
  - [ ] `video.provider.r2_count`

---

## 🆘 Emergency Rollback

If issues arise, set these environment variables immediately:

```
FALLBACK_TO_LEGACY_FLOW=true     # Use old playlist logic
SHOW_AI_ANALYSIS=false           # Skip analysis preview  
AI_REPROMPT_MAX_ATTEMPTS=0       # Disable AI reprompts
```

No service restart required - changes take effect on next request.

---

## 📊 Production Monitoring

### Key Metrics to Watch
- Video playlist build time: <2s average
- AI validation errors: <1% of requests  
- Video availability: >99.5%
- User onboarding completion: >95%

### Log Patterns to Monitor
```
INFO: Starting plan generation for user
INFO: AI whitelist cached: X exercises  
INFO: Video playlist built in Xms
ERROR: AI validation failed
ERROR: Video storage error
```

---

## 🔍 Quick Production Commands

```bash
# System health
python scripts/production_health_check.py

# Check migrations
python manage.py showmigrations workouts

# Test video storage
python manage.py shell -c "
from apps.workouts.models import VideoClip
from apps.workouts.video_storage import get_storage
vc = VideoClip.objects.filter(provider='r2').first()
if vc:
    storage = get_storage(vc)
    print(f'File exists: {storage.exists(vc)}')
    print(f'URL: {storage.playback_url(vc)[:80]}...')
"

# Check AI whitelist
python manage.py shell -c "
from apps.core.services.exercise_validation import ExerciseValidationService
for arch in ['professional', 'mentor', 'peer']:
    count = len(ExerciseValidationService.get_allowed_exercise_slugs(arch))
    print(f'{arch}: {count} exercises')
"
```

---

✅ **Ready to deploy when all environment variables are set and health check passes!**