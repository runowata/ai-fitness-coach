# Fixed v2 schema migration - works on both PostgreSQL and SQLite
# This migration ensures all v2 models and fields exist properly

from django.db import connection, migrations


def add_column_if_not_exists(apps, schema_editor):
    """Add columns using database-agnostic approach"""
    
    with connection.cursor() as cursor:
        db_vendor = connection.vendor
        
        # Define columns to add
        columns_to_add = [
            # Exercise table additions
            ('workouts_exercise', 'equipment', "VARCHAR(50) DEFAULT 'bodyweight'"),
            ('workouts_exercise', 'poster_image', "VARCHAR(100) NULL"),
            
            # VideoClip table additions  
            ('video_clips', 'r2_kind', "VARCHAR(20) DEFAULT 'technique'"),
            ('video_clips', 'r2_file', "VARCHAR(100) NULL"),
            ('video_clips', 'r2_archetype', "VARCHAR(20) DEFAULT ''"),
            ('video_clips', 'script_text', "TEXT DEFAULT ''"),
            ('video_clips', 'is_placeholder', "BOOLEAN DEFAULT FALSE"),
            
            # WorkoutPlan table addition
            ('workout_plans', 'ai_analysis', "TEXT NULL"),
        ]
        
        for table, column, definition in columns_to_add:
            try:
                if db_vendor == 'sqlite':
                    # Check if column exists in SQLite
                    cursor.execute(f"PRAGMA table_info({table})")
                    existing_columns = [row[1] for row in cursor.fetchall()]
                    
                    if column not in existing_columns:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                        
                elif db_vendor == 'postgresql':
                    # Check if column exists in PostgreSQL
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, [table, column])
                    
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                        
            except Exception as e:
                # Column might already exist or table might not exist
                print(f"Warning: Could not add {table}.{column}: {e}")


def remove_legacy_columns(apps, schema_editor):
    """Remove legacy columns safely"""
    
    with connection.cursor() as cursor:
        db_vendor = connection.vendor
        
        # Define legacy columns to remove
        columns_to_remove = [
            ('workouts_exercise', 'mistake_video_url'),
            ('workouts_exercise', 'technique_video_url'),
            ('video_clips', 'type'),
            ('video_clips', 'url'),
        ]
        
        for table, column in columns_to_remove:
            try:
                if db_vendor == 'sqlite':
                    # SQLite doesn't support DROP COLUMN easily, skip for now
                    # These will be handled by cleanup_legacy_columns command
                    pass
                    
                elif db_vendor == 'postgresql':
                    # Check if column exists before dropping
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, [table, column])
                    
                    if cursor.fetchone():
                        cursor.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}")
                        
            except Exception as e:
                # Column might not exist
                print(f"Warning: Could not remove {table}.{column}: {e}")


def add_indexes_if_not_exist(apps, schema_editor):
    """Add indexes safely"""
    
    with connection.cursor() as cursor:
        db_vendor = connection.vendor
        
        # Define indexes to create
        indexes_to_create = [
            ('idx_videoclips_r2_kind', 'video_clips', ['r2_kind']),
            ('idx_videoclips_r2_archetype', 'video_clips', ['r2_archetype']),
            ('idx_exercise_equipment', 'workouts_exercise', ['equipment']),
        ]
        
        for index_name, table, columns in indexes_to_create:
            try:
                columns_str = ', '.join(columns)
                
                if db_vendor == 'sqlite':
                    # Check if index exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", [index_name])
                    if not cursor.fetchone():
                        cursor.execute(f"CREATE INDEX {index_name} ON {table} ({columns_str})")
                        
                elif db_vendor == 'postgresql':
                    # PostgreSQL - check if index exists
                    cursor.execute("""
                        SELECT indexname FROM pg_indexes 
                        WHERE tablename = %s AND indexname = %s
                    """, [table, index_name])
                    
                    if not cursor.fetchone():
                        cursor.execute(f"CREATE INDEX {index_name} ON {table} ({columns_str})")
                        
            except Exception as e:
                print(f"Warning: Could not create index {index_name}: {e}")


class Migration(migrations.Migration):

    # This migration replaces all removed conflicting migrations
    replaces = [
        ('workouts', '0013_finalvideo_exercise_equipment_exercise_poster_image_and_more'),
        ('workouts', '0014_finalvideo_weeklylesson_and_more'),
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
            
            CREATE TABLE IF NOT EXISTS weekly_lessons (
                id bigint PRIMARY KEY,
                week smallint NOT NULL,
                archetype varchar(3) NOT NULL,
                locale varchar(5) DEFAULT 'ru',
                title varchar(120) NOT NULL,
                script text NOT NULL,
                duration_sec integer DEFAULT 180,
                CONSTRAINT unique_weekly_lesson UNIQUE (week, archetype, locale)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS final_videos; DROP TABLE IF EXISTS weekly_lessons;"
        ),
        
        # Add columns using Python functions (database-agnostic)
        migrations.RunPython(add_column_if_not_exists, migrations.RunPython.noop),
        
        # Remove legacy columns (PostgreSQL only, SQLite handled by management command)
        migrations.RunPython(remove_legacy_columns, migrations.RunPython.noop),
        
        # Add indexes
        migrations.RunPython(add_indexes_if_not_exist, migrations.RunPython.noop),
    ]