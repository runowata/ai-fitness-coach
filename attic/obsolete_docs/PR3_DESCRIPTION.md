# PR-3: feat(playlist): deterministic generation with fallbacks

## Summary
Implements deterministic video playlist generation with multi-level fallback strategy and performance optimizations to eliminate N+1 queries.

## Changes

### Core Implementation

#### 1. Fallback Constants (`apps/workouts/constants.py`)
- ✅ **Archetype Fallback Order**: professional → mentor → peer, etc.
- ✅ **Required vs Optional Videos**: technique/instruction vs mistake/intro
- ✅ **Playlist Configuration**: max candidates, retry attempts, mistake probability

#### 2. Performance Optimizations (`apps/workouts/services.py`)
- ✅ **Candidate Prefetching**: Single query loads all clips for workout
- ✅ **Memory-efficient Caching**: Limited candidates per key (20 max)
- ✅ **Deterministic Selection**: No more `order_by('?')`, RNG-based choice
- ✅ **Storage Retry Mechanism**: Up to 2 attempts if file unavailable

#### 3. Multi-Level Fallback Strategy
```
Level 1: Exact match (exercise + kind + archetype)
Level 2: Same exercise + kind, fallback archetype order  
Level 3: Similar exercise (future) - only for optional videos
```

#### 4. Enhanced Metrics (`apps/core/metrics.py`)
- ✅ `video.playlist.fallback_hit` - Level transitions
- ✅ `video.playlist.fallback_missed` - Missing optional videos
- ✅ `video.playlist.candidates_found` - Prefetch efficiency

### Configuration

```bash
# Playlist Generation (.env.example)
PLAYLIST_MISTAKE_PROB=0.30              # 0.0-1.0 chance of mistake videos
PLAYLIST_FALLBACK_MAX_CANDIDATES=20     # Memory limit per cache key
PLAYLIST_STORAGE_RETRY=2                # Storage availability retries
```

### How It Works

#### 1. Deterministic Seeding
```python
seed = hash(f"workout_{id}_{week}_{day}_{archetype}")
rng = random.Random(seed)
```
- Same workout parameters = identical playlist
- Different workouts = different results

#### 2. Prefetch Strategy
```python
# Single query for entire workout
clips = VideoClip.objects.filter(
    exercise__slug__in=exercise_ids,
    r2_kind__in=all_kinds,
    r2_archetype__in=archetype_order
).select_related('exercise')

# Group by (exercise_slug, kind, archetype)
candidates[(exercise, kind, arch)] = [clips...]
```

#### 3. Fallback Flow
```
1. Try exact match (exercise + kind + primary_archetype)
2. If not found → try fallback archetypes in order
3. If still not found:
   - Required video → ERROR + metric
   - Optional video → SKIP + metric  
4. Storage retry for each candidate (up to 2 attempts)
```

#### 4. Response Format
Each playlist item includes:
```json
{
  "type": "technique",
  "url": "https://cdn.example.com/video.mp4",
  "duration": 45,
  "clip_id": 123,
  "provider": "r2",
  "kind": "technique"
}
```

## Performance Improvements

### Before (N+1 Problem)
- 1 query per exercise per video kind
- ~10-15 queries per workout day
- Random selection via `order_by('?')`

### After (Optimized)
- 1 prefetch query for entire workout
- 1-2 additional queries for global videos (intro/closing)
- Deterministic selection via seeded RNG
- **2-4 total queries per workout** 🎯

## Fallback Examples

### Scenario 1: Missing Archetype
```
Request: push-ups + technique + professional
Level 1: No clips found
Level 2: Found push-ups + technique + mentor ✅
Result: Uses mentor's technique video
Metric: video.playlist.fallback_hit (level=2)
```

### Scenario 2: Optional Video Missing
```
Request: push-ups + mistake + professional  
Level 1: No clips found
Level 2: No fallback archetypes have it
Result: Skip mistake video gracefully
Metric: video.playlist.fallback_missed (required=false)
```

### Scenario 3: Storage Unavailable
```
Candidates: [clip_123, clip_124, clip_125]
Attempt 1: clip_123.exists() = False
Attempt 2: clip_124.exists() = True ✅  
Result: Uses clip_124
```

## Testing

### Test Coverage (`tests/test_video_playlist_deterministic.py`)
- ✅ **Determinism**: Same params = identical playlists
- ✅ **Archetype Fallback**: Level 2 fallback when primary missing
- ✅ **Optional Videos**: Graceful skip when unavailable
- ✅ **Storage Retry**: Multiple attempts for availability
- ✅ **N+1 Prevention**: Query count verification
- ✅ **Response Format**: All required fields present

### Run Tests
```bash
pytest tests/test_video_playlist_deterministic.py -v
pytest tests/test_video_playlist_deterministic.py --cov=apps.workouts.services
```

## Deployment Notes

1. **No Breaking Changes** - Backwards compatible playlist format
2. **Performance Gain** - 70% fewer DB queries for playlist generation
3. **Configurable Behavior** - All timeouts/probabilities via env vars
4. **Graceful Degradation** - Missing videos don't break playlists
5. **Monitoring** - Detailed metrics for fallback rates

## Metrics to Monitor

### Fallback Health
- `video.playlist.fallback_hit` - Should be <20% in healthy system
- `video.playlist.fallback_missed` - Should be <5% for optional videos

### Performance  
- `video.playlist.build_time_ms` - Should be <200ms typically
- `video.playlist.candidates_found` - Should match expected video count

### Quality
- Required videos missing → alerts
- High fallback rates → content gaps

## Next Steps
- PR-4: Comprehensive e2e tests
- Future: Level 3 fallback with similar exercises
- Future: Video quality scoring for better selection
- Future: A/B testing for mistake video probability