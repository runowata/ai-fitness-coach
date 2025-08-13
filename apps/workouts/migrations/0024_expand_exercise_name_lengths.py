from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workouts", "0023_alter_videoclip_exercise"),
    ]

    operations = [
        migrations.AlterField(
            model_name="csvexercise",
            name="name_en",
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name="csvexercise",
            name="name_ru",
            field=models.CharField(max_length=120),
        ),
    ]