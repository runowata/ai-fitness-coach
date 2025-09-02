# Generated manually to convert archetype values

from django.db import migrations


def convert_archetype_values(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    
    # Mapping from old numeric values to new string values
    archetype_mapping = {
        '111': 'intellectual',
        '222': 'sergeant', 
        '333': 'bro',
    }
    
    for profile in UserProfile.objects.all():
        if profile.archetype in archetype_mapping:
            profile.archetype = archetype_mapping[profile.archetype]
            profile.save(update_fields=['archetype'])

def reverse_archetype_values(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    
    # Reverse mapping
    archetype_mapping = {
        'intellectual': '111',
        'sergeant': '222',
        'bro': '333',
    }
    
    for profile in UserProfile.objects.all():
        if profile.archetype in archetype_mapping:
            profile.archetype = archetype_mapping[profile.archetype]
            profile.save(update_fields=['archetype'])

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_userprofile_archetype'),
    ]

    operations = [
        migrations.RunPython(convert_archetype_values, reverse_archetype_values),
    ]