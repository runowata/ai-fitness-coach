# Generated migration for R2 structure update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0002_add_csvexercise_model'),
    ]

    operations = [
        # Update help text for ID field (category, r2_slug, timestamps already exist in 0002)
        migrations.AlterField(
            model_name='csvexercise',
            name='id',
            field=models.CharField(primary_key=True, max_length=20, help_text='warmup_01, main_001, endurance_01, relaxation_01'),
        ),
    ]