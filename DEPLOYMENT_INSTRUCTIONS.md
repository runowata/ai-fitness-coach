# Deployment Instructions for VideoClip Fixes

## Steps to Deploy on Render:

1. **Remove duplicates before migration** (run in Render shell):
```bash
python manage.py shell -c "
from apps.workouts.models import VideoClip
from collections import Counter

# Get all URLs
urls = VideoClip.objects.values_list('url', flat=True)

# Find duplicates
duplicates = [url for url, count in Counter(urls).items() if count > 1]

print(f'Found {len(duplicates)} duplicate URLs')

# Remove duplicates, keeping only the first one
removed_count = 0
for url in duplicates:
    clips = VideoClip.objects.filter(url=url).order_by('id')
    to_delete = clips[1:]
    removed_count += len(to_delete)
    for clip in to_delete:
        clip.delete()

print(f'Removed {removed_count} duplicate VideoClip entries')

# Verify
total = VideoClip.objects.count()
unique = VideoClip.objects.values('url').distinct().count()
print(f'Total: {total}, Unique: {unique}')
"
```

2. **Apply migration**:
```bash
python manage.py migrate
```

3. **Run the updated create_video_clips command**:
```bash
python manage.py create_video_clips
```

4. **Verify the fix**:
```bash
python manage.py shell -c "
from apps.workouts.models import VideoClip
print('Total VideoClips:', VideoClip.objects.count())
print('Unique URLs:', VideoClip.objects.values('url').distinct().count())
"
```

5. **Restart the service**:
```bash
kill -HUP 1
```

## What was fixed:

1. **Fixed duplicate URL creation**: Changed `get_or_create` to use `url` as the lookup field
2. **Added unique constraint**: Made `url` field unique in VideoClip model
3. **Removed non-existent field reference**: No references to `slug` field which doesn't exist

## Alternative if migration fails:

If the migration fails due to existing duplicates, you can use the provided `remove_videoclip_duplicates.py` script locally and then migrate.