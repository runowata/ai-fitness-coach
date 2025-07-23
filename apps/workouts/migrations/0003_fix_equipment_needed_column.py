from django.db import migrations

def add_equipment_needed_if_missing(apps, schema_editor):
    """Add equipment_needed column if it doesn't exist - PostgreSQL specific fix"""
    from django.db import connection
    
    # Only run on PostgreSQL
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'exercises'
                AND column_name = 'equipment_needed'
            );
        """)
        
        if not cursor.fetchone()[0]:
            # Column doesn't exist, add it
            cursor.execute("""
                ALTER TABLE exercises 
                ADD COLUMN IF NOT EXISTS equipment_needed JSONB DEFAULT '[]';
            """)

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('workouts', '0002_convert_exercise_id_to_varchar'),
    ]

    operations = [
        migrations.RunPython(add_equipment_needed_if_missing, reverse_func),
    ]