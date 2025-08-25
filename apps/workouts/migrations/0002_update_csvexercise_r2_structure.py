# Generated migration for R2 structure update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0001_initial'),
    ]

    operations = [
        # Add new fields for R2 structure support
        migrations.AddField(
            model_name='csvexercise',
            name='category',
            field=models.CharField(blank=True, max_length=20, help_text='warmup / main / endurance / relaxation'),
        ),
        migrations.AddField(
            model_name='csvexercise',
            name='r2_slug',
            field=models.CharField(blank=True, max_length=50, help_text='Original R2 slug format'),
        ),
        migrations.AddField(
            model_name='csvexercise',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='csvexercise',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, blank=True, null=True),
        ),
        
        # Update field lengths and help texts
        migrations.AlterField(
            model_name='csvexercise',
            name='id',
            field=models.CharField(primary_key=True, max_length=20, help_text='warmup_01, main_001, endurance_01, relaxation_01'),
        ),
        migrations.AlterField(
            model_name='csvexercise',
            name='exercise_type',
            field=models.CharField(blank=True, max_length=120, help_text='strength / mobility / cardio / flexibility'),
        ),
        migrations.AlterField(
            model_name='csvexercise',
            name='muscle_group',
            field=models.CharField(blank=True, max_length=120, help_text='Все тело / Грудь / Спина / Ноги / и т.д.'),
        ),
    ]