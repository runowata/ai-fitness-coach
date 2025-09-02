# 🚀 Production Deployment Checklist

## Pre-Flight Check (1-2 hours)

### 1. Environment Configuration ✅
```bash
# R2 Video Storage (choose one)
R2_SIGNED_URLS=true
R2_SIGNED_URL_TTL=3600
# OR for CDN
# R2_CDN_BASE_URL=https://cdn.your-domain.com
# R2_SIGNED_URLS=false

# AI Configuration
SHOW_AI_ANALYSIS=true
AI_REPROMPT_MAX_ATTEMPTS=2
PLAYLIST_MISTAKE_PROB=0.30
FALLBACK_TO_LEGACY_FLOW=false

# Credentials (minimal permissions)
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=your-r2-access-key
AWS_SECRET_ACCESS_KEY=your-r2-secret-key
AWS_S3_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=ai-fitness-media

# Metrics
METRICS_BACKEND=logging  # or statsd/otel
```

### 2. Database Migrations ✅
```bash
# Check migration status
python manage.py showmigrations workouts

# Should show:
# [X] 0016_add_video_provider_fields
# [X] 0017_add_provider_constraints  
# [X] 0018_fix_unique_constraint_archetype_field
# [X] 0019_remove_videoclip_provider_storage_consistency_and_more
```

### 3. Data Backfill (One-time) ✅
```bash
# Set provider for existing R2 clips
python manage.py shell -c "
from apps.workouts.models import VideoClip
count = VideoClip.objects.filter(r2_file__isnull=False).update(provider='r2')
print(f'Updated {count} clips with provider=r2')
"

# Warm up whitelist caches (optional)
python manage.py shell -c "
from apps.core.services.exercise_validation import ExerciseValidationService as S
for archetype in ['peer', 'professional', 'mentor']:
    count = len(S.get_allowed_exercise_slugs(archetype))
    print(f'{archetype}: {count} allowed exercises')
print('Whitelist caches warmed')
"
```

### 4. Production Smoke Tests ✅

#### Core User Flow
- [ ] **Onboarding** → Analysis shows → Confirm → Plan created
- [ ] **First workout** → Playlist loads (intro/technique/instruction)
- [ ] **Rest day** → Weekly/closing videos present
- [ ] **Video URLs** → All return 200 status

#### Metrics Validation
Check logs for these metrics:
- [ ] `ai.whitelist.exercises_count`
- [ ] `ai.plan.exercises_substituted` 
- [ ] `video.provider.r2_count`
- [ ] `video.playlist.build_time_ms`
- [ ] `video.playlist.fallback_*`

### 5. Monitoring & Alerts ✅
```bash
# Critical alerts to set up:
- ai.validation.failed > 0 (RED ALERT)
- video.playlist.fallback_missed > 10/min
- video.playlist.build_time_ms p95 > 5000ms
- video.storage.error_rate > 1%
```

### 6. CI/PR Process ✅
- [ ] GitHub Actions required for merge
- [ ] PR template active
- [ ] CODEOWNERS assigning reviewers
- [ ] Branch protection: 85%+ coverage required

### 7. Rollback Plan 🆘
```bash
# Emergency rollback options:
FALLBACK_TO_LEGACY_FLOW=true      # Use old playlist logic
SHOW_AI_ANALYSIS=false            # Skip analysis preview
AI_REPROMPT_MAX_ATTEMPTS=0        # Disable reprompts

# Restart services after config change
```

---

## ⚡ Production Health Check (10 minutes)

### Quick Validation Endpoints

```bash
# 1. System Health
curl https://your-app.com/healthz/
# Expected: {"status": "ok", "checks": {...}}

# 2. Admin Panel Access
curl -I https://your-app.com/admin/
# Expected: 302 redirect to login

# 3. Static Files
curl -I https://your-app.com/static/admin/css/base.css
# Expected: 200 OK

# 4. API Endpoints
curl -I https://your-app.com/api/weekly/current/
# Expected: 200 OK (or 401 if auth required)
```

### Video Storage Test
```python
# Quick manual test
python manage.py shell -c "
from apps.workouts.models import VideoClip
from apps.workouts.video_storage import get_storage

vc = VideoClip.objects.filter(provider='r2').first()
if vc:
    storage = get_storage(vc)
    exists = storage.exists(vc)
    url = storage.playback_url(vc)
    print(f'Clip: {vc.r2_file}')
    print(f'Exists: {exists}')
    print(f'URL: {url[:80]}...')
else:
    print('No R2 clips found')
"
```

### AI Generation Test
```python
# Test workout plan generation
python manage.py shell -c "
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.core.services.exercise_validation import ExerciseValidationService

# Check whitelist size
allowed = ExerciseValidationService.get_allowed_exercise_slugs('professional')
print(f'Professional whitelist: {len(allowed)} exercises')

# Test AI client (mock data)
generator = WorkoutPlanGenerator()
print(f'Generator initialized: {generator.__class__.__name__}')
print('AI system ready')
"
```

### Performance Baseline
```bash
# Measure key operations
time curl -s https://your-app.com/ > /dev/null
time curl -s https://your-app.com/users/dashboard/ > /dev/null

# Database query count (run in Django admin or shell)
# Should be <5 queries for dashboard load
```

---

## 📊 Success Metrics (Week 1)

- **User Flow**: >95% onboarding completion rate
- **Video Delivery**: <2s average playlist build time  
- **AI Quality**: <5% exercises requiring substitution
- **Storage**: 99.9% video availability
- **Zero**: Critical errors or 500s

---

## 🆘 Emergency Contacts

- **Primary:** @alexbel
- **Backend:** @backend-team  
- **Infrastructure:** @devops-team
- **On-call:** [Your monitoring system]

---

✅ **Ready for production when all checkboxes are complete!**