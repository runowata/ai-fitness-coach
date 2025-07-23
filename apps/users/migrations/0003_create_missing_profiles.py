from django.db import migrations

def create_missing_user_profiles(apps, schema_editor):
    """Create UserProfile for all users that don't have one"""
    User = apps.get_model('users', 'User')
    UserProfile = apps.get_model('users', 'UserProfile')
    
    # Find all users without profiles
    users_without_profiles = User.objects.filter(profile__isnull=True)
    
    # Create profiles for them
    for user in users_without_profiles:
        UserProfile.objects.create(
            user=user,
            archetype='',  # Will be set during onboarding
            notification_time='08:00',
            push_notifications_enabled=True,
            email_notifications_enabled=True,
            experience_points=0,
            level=1,
            total_workouts_completed=0,
            current_streak=0,
            longest_streak=0
        )
    
    print(f"Created {users_without_profiles.count()} missing user profiles")

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_fix_user_profiles_table'),
    ]

    operations = [
        migrations.RunPython(create_missing_user_profiles, reverse_func),
    ]