# PR-1: feat(video): multi-provider storage with CDN support

## Summary
Implements multi-provider video storage abstraction layer with CDN and signed URL support for flexible video delivery.

## Changes

### Core Implementation
- ✅ Added environment variables for video configuration in `config/settings.py`:
  - `SHOW_AI_ANALYSIS`, `AI_REPROMPT_MAX_ATTEMPTS`, `FALLBACK_TO_LEGACY_FLOW`
  - `R2_CDN_BASE_URL`, `R2_SIGNED_URLS`, `R2_SIGNED_URL_TTL`
  - `METRICS_BACKEND` for metrics collection

- ✅ Created metrics collection module (`apps/core/metrics.py`):
  - Abstraction over StatsD/OpenTelemetry/logging
  - Standard metric names for consistency
  - Timer decorator and context manager

- ✅ Enhanced video storage adapters (`apps/workouts/video_storage.py`):
  - R2Adapter with CDN and signed URL support
  - StreamAdapter for Cloudflare Stream HLS
  - ExternalAdapter for future extensibility
  - Factory function `get_storage()` for adapter selection

- ✅ Updated `VideoPlaylistBuilder` service:
  - Added metrics collection (build time, provider counts)
  - Provider information in playlist items
  - Deterministic RNG already implemented

- ✅ Added fallback priority constants (`apps/workouts/constants.py`):
  - `EXERCISE_FALLBACK_PRIORITY` for substitution order

### Database
- ✅ Migrations already in place:
  - `0016_add_video_provider_fields.py` - provider field
  - `0017_add_provider_constraints.py` - consistency constraints

### Tests
- ✅ Comprehensive test suite (`tests/test_video_storage_adapters.py`):
  - Unit tests for all adapters
  - CDN URL generation
  - Signed URL generation with fallback
  - Integration tests with real models

## Configuration

### Required Environment Variables
```bash
# Video Storage
R2_CDN_BASE_URL=https://cdn.example.com  # Optional: CDN domain
R2_SIGNED_URLS=true                      # Optional: Enable signed URLs
R2_SIGNED_URL_TTL=3600                   # Optional: TTL in seconds

# Metrics
METRICS_BACKEND=statsd  # Options: statsd, logging, noop

# Feature Flags
SHOW_AI_ANALYSIS=true
AI_REPROMPT_MAX_ATTEMPTS=2
FALLBACK_TO_LEGACY_FLOW=false
```

## Testing
```bash
# Run video storage tests
pytest tests/test_video_storage_adapters.py -v

# Run with coverage
pytest tests/test_video_storage_adapters.py --cov=apps.workouts.video_storage

# Integration tests
pytest tests/test_video_storage_adapters.py -m integration
```

## Metrics Collected
- `video.playlist.build_time_ms` - Playlist generation time
- `video.provider.r2_count` - R2 videos served
- `video.provider.stream_count` - Stream videos served
- `video.signed_url.generated` - Signed URLs generated

## Deployment Notes
1. No breaking changes - fully backwards compatible
2. CDN and signed URLs are optional (off by default)
3. Metrics are in logging mode for development, noop for production
4. All existing video clips work without modification

## Next Steps
- PR-2: Strict AI exercise validation with whitelist
- PR-3: Deterministic playlist generation improvements
- PR-4: Comprehensive e2e test coverage