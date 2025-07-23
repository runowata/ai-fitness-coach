from django.db import migrations, connection

SQL = """
ALTER TABLE exercises
  ALTER COLUMN id        TYPE integer USING id::integer,
  ALTER COLUMN exercise_id TYPE integer USING exercise_id::integer;

ALTER TABLE workouts_plan_exercises
  ALTER COLUMN exercise_id TYPE integer USING exercise_id::integer;
"""

class Migration(migrations.RunSQL):
    run_sql = migrations.RunSQL.noop

    def apply(self, project_state, schema_editor, collect_sql=False):
        with connection.cursor() as c:
            c.execute(SQL)
        return project_state

    def unapply(self, project_state, schema_editor, collect_sql=False):
        pass
PY < /dev/null