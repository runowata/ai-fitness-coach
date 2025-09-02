from django.db import migrations


def forwards_func(apps, schema_editor):
    """Convert string archetypes to numeric codes"""
    UserProfile = apps.get_model("users", "UserProfile")
    
    # Map old string values to new numeric codes
    archetype_map = {
        "bro": "333",           # Ровесник
        "sergeant": "222",      # Профессионал  
        "intellectual": "111",  # Наставник
    }
    
    for old_value, new_value in archetype_map.items():
        UserProfile.objects.filter(archetype=old_value).update(archetype=new_value)
    
    print(f"Migrated archetype codes: {archetype_map}")


def reverse_func(apps, schema_editor):
    """Reverse migration - convert numeric codes back to strings"""
    UserProfile = apps.get_model("users", "UserProfile")
    
    # Reverse map
    reverse_map = {
        "333": "bro",
        "222": "sergeant", 
        "111": "intellectual",
    }
    
    for old_value, new_value in reverse_map.items():
        UserProfile.objects.filter(archetype=old_value).update(archetype=new_value)


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_userprofile_alcohol_consumption_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]