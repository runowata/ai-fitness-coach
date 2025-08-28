from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('achievements','0001_initial')]
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # колонка уже есть в БД
            state_operations=[
                migrations.AddField(
                    model_name='achievement',
                    name='slug',
                    field=models.SlugField(max_length=120, unique=True, db_index=True),
                ),
            ],
        ),
    ]