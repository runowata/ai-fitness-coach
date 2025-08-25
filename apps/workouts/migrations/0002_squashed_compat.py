# Squashed migration to replace all workouts migrations 0002-0025
from django.db import migrations, connection

class Migration(migrations.Migration):
    
    dependencies = [
        ('workouts', '0001_initial'),
    ]

    # Converted from squashed migration to normal migration

    def ensure_production_schema(apps, schema_editor):
        """Idempotent DDL to fix WorkoutPlan.name column"""
        
        WorkoutPlan = apps.get_model("workouts", "WorkoutPlan")
        table_name = WorkoutPlan._meta.db_table
        
        with connection.cursor() as cursor:
            # Check if name column exists - different approach for different DB engines
            column_exists = False
            
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'name'
                    LIMIT 1
                """, [table_name])
                column_exists = cursor.fetchone() is not None
            else:
                # SQLite - use PRAGMA table_info
                cursor.execute(f'PRAGMA table_info({table_name})')
                columns = [row[1] for row in cursor.fetchall()]
                column_exists = 'name' in columns
            
            if not column_exists:
                # Add missing name column with default - safe for both PostgreSQL and SQLite
                if connection.vendor == 'postgresql':
                    cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "name" VARCHAR(200) NOT NULL DEFAULT %s', ['Персональный план'])
                else:
                    # SQLite
                    cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "name" VARCHAR(200) NOT NULL DEFAULT %s', ['Персональный план'])
    
    # Операции: no-op для истории + DDL исправления для продакшена
    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
        migrations.RunPython(ensure_production_schema, migrations.RunPython.noop),
    ]
    
    atomic = False