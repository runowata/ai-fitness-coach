# Merge migration to resolve conflicting 0002 migrations

from django.db import migrations


class Migration(migrations.Migration):
    
    dependencies = [
        ('workouts', '0002_add_csvexercise_model'),
        ('workouts', '0002_squashed_compat'),
    ]
    
    operations = [
        # No operations needed - just merging two branches
    ]