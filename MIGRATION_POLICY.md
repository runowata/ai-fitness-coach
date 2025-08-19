# Migration Policy

This document outlines the migration practices for the AI Fitness Coach project to prevent schema synchronization issues and deployment failures.

## Core Principles

1. **Idempotent Migrations**: All migrations must be safe to run multiple times
2. **Production-Safe DDL**: Never assume schema state in production
3. **Two-Step Non-Null Changes**: Add nullable first, then make non-null separately
4. **Consistent Table Names**: Always use explicit `db_table` names

## Required Patterns

### 1. Adding New Fields

❌ **NEVER** use simple `AddField` for production deployments:
```python
migrations.AddField(
    model_name='workoutplan',
    name='new_field',
    field=models.CharField(max_length=100),
)
```

✅ **ALWAYS** use `SeparateDatabaseAndState` with `IF NOT EXISTS`:
```python
migrations.SeparateDatabaseAndState(
    database_operations=[
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF to_regclass('public.workout_plans') IS NOT NULL THEN
                    ALTER TABLE workout_plans
                    ADD COLUMN IF NOT EXISTS new_field VARCHAR(100);
                ELSIF to_regclass('public.workouts_workoutplan') IS NOT NULL THEN
                    ALTER TABLE workouts_workoutplan
                    ADD COLUMN IF NOT EXISTS new_field VARCHAR(100);
                END IF;
            END
            $$;
            """,
            reverse_sql="""
            DO $$
            BEGIN
                IF to_regclass('public.workout_plans') IS NOT NULL THEN
                    ALTER TABLE workout_plans
                    DROP COLUMN IF EXISTS new_field;
                ELSIF to_regclass('public.workouts_workoutplan') IS NOT NULL THEN
                    ALTER TABLE workouts_dailyworkout
                    DROP COLUMN IF EXISTS new_field;
                END IF;
            END
            $$;
            """,
        ),
    ],
    state_operations=[
        migrations.AddField(
            model_name='workoutplan',
            name='new_field',
            field=models.CharField(max_length=100),
        ),
    ],
),
```

### 2. Non-Null Fields (Two-Step Process)

Step 1: Add as nullable with default
```python
migrations.SeparateDatabaseAndState(
    database_operations=[
        migrations.RunSQL(
            sql="ALTER TABLE workout_plans ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft';",
            reverse_sql="ALTER TABLE workout_plans DROP COLUMN IF EXISTS status;",
        ),
    ],
    state_operations=[
        migrations.AddField(
            model_name='workoutplan',
            name='status',
            field=models.CharField(max_length=20, default='draft'),
        ),
    ],
),
```

Step 2: (In separate migration) Make non-null after data population
```python
migrations.RunSQL(
    sql="ALTER TABLE workout_plans ALTER COLUMN status SET NOT NULL;",
    reverse_sql="ALTER TABLE workout_plans ALTER COLUMN status DROP NOT NULL;",
),
```

### 3. Table Names

All models MUST specify explicit `db_table`:
```python
class WorkoutPlan(models.Model):
    # ... fields ...
    
    class Meta:
        db_table = 'workout_plans'  # Explicit table name
```

### 4. Indexes and Constraints

Use `IF NOT EXISTS` / `IF EXISTS` patterns:
```python
migrations.RunSQL(
    sql="""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'idx_workout_plans_user_active'
            AND n.nspname = 'public'
        ) THEN
            CREATE INDEX idx_workout_plans_user_active 
            ON workout_plans(user_id, is_active);
        END IF;
    END
    $$;
    """,
    reverse_sql="DROP INDEX IF EXISTS idx_workout_plans_user_active;",
),
```

## CI/CD Integration

The project includes migration guards that:

1. **Fresh Database Test**: Runs all migrations on empty database
2. **Existing Schema Test**: Tests migrations against prod-like schema
3. **Idempotency Test**: Ensures migrations can run multiple times safely

### Local Testing

Before creating PR:
```bash
# Test on fresh database
dropdb ai_fitness_test || true
createdb ai_fitness_test
python manage.py migrate

# Test idempotency
python manage.py migrate

# Check for new migrations
python manage.py makemigrations --check
```

## Squashed Migrations

The project uses squashed migrations as baseline:
- `0001_initial_squashed_*.py` represents the canonical schema
- Apply in production with: `python manage.py migrate --fake-initial`
- Old individual migrations are kept for reference but not used

## Emergency Procedures

If migration fails in production:

1. **DO NOT** manually alter schema in database
2. Create hotfix migration with proper `IF NOT EXISTS` patterns
3. Test locally first with existing schema
4. Deploy hotfix migration

## Common PostgreSQL Data Types

| Django Field | PostgreSQL Type | SQL Example |
|--------------|----------------|-------------|
| `CharField(max_length=100)` | `VARCHAR(100)` | `VARCHAR(100)` |
| `TextField()` | `TEXT` | `TEXT` |
| `IntegerField()` | `INTEGER` | `INTEGER` |
| `BooleanField()` | `BOOLEAN` | `BOOLEAN` |
| `DateTimeField()` | `TIMESTAMPTZ` | `TIMESTAMPTZ` |
| `JSONField()` | `JSONB` | `JSONB` |

## Table Name Reference

| Model | Table Name |
|-------|------------|
| `WorkoutPlan` | `workout_plans` |
| `DailyWorkout` | `daily_workouts` |
| `Exercise` | `exercises` |
| `User` | `users` |
| `UserProfile` | `user_profiles` |

## Questions?

When in doubt:
1. Check existing migrations for patterns
2. Test with both fresh and existing schemas locally
3. Use `SeparateDatabaseAndState` + `IF NOT EXISTS` for safety
4. Ask for review if unsure about complex schema changes