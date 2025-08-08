# Fix v2 schema issues after migration conflicts
# This migration ensures all v2 models and fields exist properly

from django.db import migrations, models


class Migration(migrations.Migration):

    # This migration replaces all removed conflicting migrations
    replaces = [
        ('workouts', '0013_finalvideo_exercise_equipment_exercise_poster_image_and_more'),
        ('workouts', '0014_clean_v1_legacy'),
        ('workouts', '0015_add_v2_indexes'),
        ('workouts', '0016_v2_schema'),
    ]

    dependencies = [
        ('workouts', '0012_add_duration_sec_field'),
    ]

    operations = [
        # Create v2 tables
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
        
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS weekly_lessons (
                id BIGSERIAL PRIMARY KEY,
                week smallint,
                archetype varchar(20),
                locale varchar(5) DEFAULT 'ru',
                title varchar(120),
                script text,
                duration_sec integer DEFAULT 180,
                CONSTRAINT weekly_lessons_week_archetype_locale_uniq UNIQUE (week, archetype, locale)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS weekly_lessons;"
        ),

        # Add missing fields to existing tables (safe for clean DB)
        migrations.RunSQL(
            sql="""
            -- Add v2 fields to exercises table if table and columns don't exist
            DO $$ 
            BEGIN
                IF to_regclass('public.workouts_exercise') IS NOT NULL THEN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workouts_exercise' AND column_name='equipment') THEN
                        ALTER TABLE workouts_exercise ADD COLUMN equipment varchar(50) DEFAULT 'bodyweight';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workouts_exercise' AND column_name='poster_image') THEN
                        ALTER TABLE workouts_exercise ADD COLUMN poster_image varchar(100);
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),

        # Add v2 fields to videoclip table (safe for clean DB)
        migrations.RunSQL(
            sql="""
            -- Add v2 fields to videoclips table if table exists and columns don't exist
            DO $$ 
            BEGIN
                IF to_regclass('public.video_clips') IS NOT NULL THEN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_kind') THEN
                        ALTER TABLE video_clips ADD COLUMN r2_kind varchar(20) DEFAULT '';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_file') THEN
                        ALTER TABLE video_clips ADD COLUMN r2_file varchar(100);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_archetype') THEN
                        ALTER TABLE video_clips ADD COLUMN r2_archetype varchar(20);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='script_text') THEN
                        ALTER TABLE video_clips ADD COLUMN script_text text;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='is_placeholder') THEN
                        ALTER TABLE video_clips ADD COLUMN is_placeholder boolean DEFAULT false;
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),

        # Add v2 fields to workoutplan table (safe for clean DB)
        migrations.RunSQL(
            sql="""
            -- Add ai_analysis to workoutplan table if table exists and column doesn't exist
            DO $$ 
            BEGIN
                IF to_regclass('public.workout_plans') IS NOT NULL THEN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workout_plans' AND column_name='ai_analysis') THEN
                        ALTER TABLE workout_plans ADD COLUMN ai_analysis jsonb;
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),

        # Remove legacy fields if they exist (safe for clean DB)
        migrations.RunSQL(
            sql="""
            -- Remove legacy v1 fields from exercises table if table exists
            DO $$ 
            BEGIN
                IF to_regclass('public.workouts_exercise') IS NOT NULL THEN
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workouts_exercise' AND column_name='technique_video_url') THEN
                        ALTER TABLE workouts_exercise DROP COLUMN technique_video_url;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='workouts_exercise' AND column_name='mistake_video_url') THEN
                        ALTER TABLE workouts_exercise DROP COLUMN mistake_video_url;
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),

        # Remove legacy fields from videoclip table (safe for clean DB)
        migrations.RunSQL(
            sql="""
            -- Remove legacy v1 fields from video_clips table if table exists
            DO $$ 
            BEGIN
                IF to_regclass('public.video_clips') IS NOT NULL THEN
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='type') THEN
                        ALTER TABLE video_clips DROP COLUMN type;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='url') THEN
                        ALTER TABLE video_clips DROP COLUMN url;
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),

        # Create v2 indexes (safe for clean DB - check columns exist)
        migrations.RunSQL(
            sql="""
            -- Create v2 indexes if table and columns exist and indexes don't exist
            DO $$
            BEGIN
                -- Index on exercise_id, r2_kind, r2_archetype (not archetype)
                IF to_regclass('public.video_clips') IS NOT NULL 
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='exercise_id')
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_kind')
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_archetype') THEN
                    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'video_clips_exercis_1e5613_idx') THEN
                        CREATE INDEX video_clips_exercis_1e5613_idx ON video_clips(exercise_id, r2_kind, r2_archetype);
                    END IF;
                END IF;
                
                -- Index on r2_kind, r2_archetype
                IF to_regclass('public.video_clips') IS NOT NULL 
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_kind')
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_archetype') THEN
                    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'video_clips_r2_kind_d2e4dd_idx') THEN
                        CREATE INDEX video_clips_r2_kind_d2e4dd_idx ON video_clips(r2_kind, r2_archetype);
                    END IF;
                END IF;
                
                -- Index on is_active, r2_kind
                IF to_regclass('public.video_clips') IS NOT NULL 
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='is_active')
                   AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='video_clips' AND column_name='r2_kind') THEN
                    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'video_clips_is_acti_9705f9_idx') THEN
                        CREATE INDEX video_clips_is_acti_9705f9_idx ON video_clips(is_active, r2_kind);
                    END IF;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]