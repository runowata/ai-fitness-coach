# Generated manually to fix video URLs
from django.db import migrations


def fix_video_urls(apps, schema_editor):
    """Convert /media/videos/ URLs to /static/videos/ URLs"""
    VideoClip = apps.get_model('workouts', 'VideoClip')
    
    # Get all clips with /media/ URLs
    clips = VideoClip.objects.filter(url__startswith='/media/videos/')
    updated_count = 0
    
    for clip in clips:
        old_url = clip.url
        # Convert /media/videos/... to /static/videos/...
        new_url = old_url.replace('/media/videos/', '/static/videos/')
        clip.url = new_url
        clip.save()
        updated_count += 1
        
        if updated_count <= 5:
            print(f'Updated: {old_url} -> {new_url}')
    
    print(f'Total updated: {updated_count} video URLs from /media/ to /static/')


def reverse_video_urls(apps, schema_editor):
    """Reverse operation - convert back to /media/"""
    VideoClip = apps.get_model('workouts', 'VideoClip')
    
    clips = VideoClip.objects.filter(url__startswith='/static/videos/')
    for clip in clips:
        clip.url = clip.url.replace('/static/videos/', '/media/videos/')
        clip.save()


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0006_exercise_equipment'),
    ]

    operations = [
        migrations.RunPython(fix_video_urls, reverse_video_urls),
    ]