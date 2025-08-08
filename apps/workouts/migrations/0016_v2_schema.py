# Fix v2 schema issues after migration conflicts
# This migration ensures all v2 models and fields exist properly

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0015_add_v2_indexes'),
    ]

    operations = [
        # Ensure FinalVideo table exists with correct schema
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS final_videos (
                arch varchar(20) PRIMARY KEY,
                locale varchar(5) DEFAULT 'ru',
                script text
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS final_videos;"
        ),
        
        # Ensure WeeklyLesson table exists with correct schema  
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS weekly_lessons (
                id bigint PRIMARY KEY,
                week smallint,
                archetype varchar(20),
                locale varchar(5) DEFAULT 'ru',
                title varchar(120),
                script text,
                duration_sec integer DEFAULT 180
            );
            
            -- Add unique constraint if it doesn't exist
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'weekly_lessons_week_archetype_locale_uniq'
                ) THEN
                    ALTER TABLE weekly_lessons 
                    ADD CONSTRAINT weekly_lessons_week_archetype_locale_uniq 
                    UNIQUE (week, archetype, locale);
                END IF;
            END $$;
            """,
            reverse_sql="DROP TABLE IF EXISTS weekly_lessons;"
        ),
    ]