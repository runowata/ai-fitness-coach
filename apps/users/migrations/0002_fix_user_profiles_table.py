from django.db import migrations

def create_user_profiles_if_missing(apps, schema_editor):
    """Create user_profiles table if it doesn't exist - PostgreSQL specific fix"""
    from django.db import connection
    
    # Only run on PostgreSQL
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_profiles'
            );
        """)
        
        if not cursor.fetchone()[0]:
            # Table doesn't exist, run the SQL to create it
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id BIGSERIAL PRIMARY KEY,
                    archetype VARCHAR(20),
                    age INTEGER,
                    height INTEGER,
                    weight INTEGER,
                    goals JSONB DEFAULT '{}',
                    limitations JSONB DEFAULT '{}',
                    experience_points INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    notification_time TIME DEFAULT '08:00:00',
                    push_notifications_enabled BOOLEAN DEFAULT TRUE,
                    email_notifications_enabled BOOLEAN DEFAULT TRUE,
                    onboarding_completed_at TIMESTAMP WITH TIME ZONE,
                    last_workout_at TIMESTAMP WITH TIME ZONE,
                    total_workouts_completed INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE
                );
            """)
            
            # Create index on user_id
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS user_profiles_user_id_idx ON user_profiles(user_id);
            """)

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_user_profiles_if_missing, reverse_func),
    ]