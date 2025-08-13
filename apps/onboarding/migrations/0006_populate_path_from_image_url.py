# Generated manually for migrating image_url to path field

from django.db import migrations
import re


def extract_path_from_url(url):
    """Extract relative path from R2 public URL"""
    if not url or not url.startswith('http'):
        return ''
    
    # Match pattern: https://pub-{hash}.r2.dev/{path}
    match = re.search(r'https://pub-[a-f0-9]+\.r2\.dev/(.+)', url)
    if match:
        return match.group(1)
    
    return ''


def populate_path_field(apps, schema_editor):
    """Populate path field from image_url field"""
    MotivationalCard = apps.get_model('onboarding', 'MotivationalCard')
    
    updated_count = 0
    for card in MotivationalCard.objects.all():
        if card.image_url and not card.path:
            # Extract path from image_url
            path = extract_path_from_url(card.image_url)
            if path:
                card.path = path
                card.save(update_fields=['path'])
                updated_count += 1
    
    print(f"Populated path field for {updated_count} MotivationalCard records")


def reverse_populate_path_field(apps, schema_editor):
    """Reverse migration - clear path field"""
    MotivationalCard = apps.get_model('onboarding', 'MotivationalCard')
    MotivationalCard.objects.update(path='')


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0005_motivationalcard_path_alter_motivationalcard_image_and_more'),
    ]

    operations = [
        migrations.RunPython(
            populate_path_field,
            reverse_populate_path_field,
        ),
    ]