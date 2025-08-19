# Generated manually to add updated_at field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0003_add_missing_question_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='motivationalcard',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]