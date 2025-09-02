from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("workouts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='poster_image',
            field=models.CharField(max_length=500, null=True, blank=True),
        ),
    ]