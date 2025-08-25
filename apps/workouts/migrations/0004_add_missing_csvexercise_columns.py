# Add missing columns to existing csv_exercises table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0003_update_csvexercise_r2_structure'),
    ]

    operations = [
        # Add missing columns that exist in model but not in production DB
        migrations.RunSQL(
            sql=[
                # Add category column
                "ALTER TABLE csv_exercises ADD COLUMN IF NOT EXISTS category VARCHAR(20) DEFAULT '';",
                # Add r2_slug column  
                "ALTER TABLE csv_exercises ADD COLUMN IF NOT EXISTS r2_slug VARCHAR(50) DEFAULT '';",
                # Add timestamps
                "ALTER TABLE csv_exercises ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
                "ALTER TABLE csv_exercises ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
                # Update existing records to have timestamps
                "UPDATE csv_exercises SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;",
                "UPDATE csv_exercises SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;",
            ],
            reverse_sql=[
                "ALTER TABLE csv_exercises DROP COLUMN IF EXISTS category;",
                "ALTER TABLE csv_exercises DROP COLUMN IF EXISTS r2_slug;",
                "ALTER TABLE csv_exercises DROP COLUMN IF EXISTS created_at;",
                "ALTER TABLE csv_exercises DROP COLUMN IF EXISTS updated_at;",
            ],
        ),
    ]