from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE users
              ADD COLUMN IF NOT EXISTS completed_onboarding boolean
              DEFAULT FALSE
              NOT NULL;
            """,
            reverse_sql="""
            ALTER TABLE users
              DROP COLUMN IF EXISTS completed_onboarding;
            """,
        ),
    ]
