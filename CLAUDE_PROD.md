# Production Quick Commands

## Health & Monitoring
```bash
# Complete system health check
python scripts/production_health_check.py

# Quick component checks  
python manage.py shell -c "from apps.workouts.video_storage import get_storage; print('✅ Storage adapters ready')"
python manage.py shell -c "from apps.core.services.exercise_validation import ExerciseValidationService; print(f'✅ Whitelist: {len(ExerciseValidationService.get_allowed_exercise_slugs())} exercises')"
```

## Deployment Commands
```bash
# Pre-deployment validation
python manage.py check --deploy
python manage.py showmigrations workouts  
python manage.py collectstatic --noinput

# One-time data backfill
python manage.py shell -c "from apps.workouts.models import VideoClip; VideoClip.objects.filter(r2_file__isnull=False).update(provider='r2')"

# Performance baseline
python manage.py shell -c "
import time
from apps.workouts.services import VideoPlaylistBuilder
start = time.time()
builder = VideoPlaylistBuilder('professional')  
print(f'✅ Init time: {(time.time()-start)*1000:.1f}ms')
"
```

## Production Environment
```bash
# Critical settings
R2_SIGNED_URLS=true
R2_SIGNED_URL_TTL=3600
SHOW_AI_ANALYSIS=true
AI_REPROMPT_MAX_ATTEMPTS=2
PLAYLIST_MISTAKE_PROB=0.30
FALLBACK_TO_LEGACY_FLOW=false

# Emergency rollback
FALLBACK_TO_LEGACY_FLOW=true  # Immediate fallback without restart
SHOW_AI_ANALYSIS=false        # Skip analysis if blocking users
```

## Monitoring Metrics
- `ai.whitelist.exercises_count` - Whitelist size per archetype
- `ai.plan.exercises_substituted` - AI validation failures  
- `video.playlist.build_time_ms` - Performance tracking
- `video.provider.r2_count` - Storage distribution
- `video.playlist.fallback_*` - Fallback usage patterns

## Emergency Contacts
- Primary: @alexbel
- Render Dashboard: https://dashboard.render.com
- Health Check: `python scripts/production_health_check.py`