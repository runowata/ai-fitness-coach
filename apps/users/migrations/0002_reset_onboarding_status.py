# Generated migration to reset onboarding status

from django.db import migrations

def reset_onboarding_status(apps, schema_editor):
    """Reset onboarding status for all users to allow them to go through onboarding again"""
    User = apps.get_model('users', 'User')
    
    # Reset onboarding completion for all users
    User.objects.update(onboarding_completed_at=None)
    
    print(f"Reset onboarding status for {User.objects.count()} users")

def reverse_reset_onboarding_status(apps, schema_editor):
    """Reverse migration - do nothing"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            reset_onboarding_status,
            reverse_reset_onboarding_status,
        ),
    ]