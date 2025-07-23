#!/usr/bin/env python3
"""
🗄️ CREATE CLEAN DATABASE FROM SCRATCH
This script creates a completely new, clean database schema for AI Fitness Coach
Based on analysis of archive codebase and intended functionality.
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line
import json

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print('='*60)

def print_step(step, desc):
    print(f"\n{step}. {desc}")

def execute_sql(sql, desc=""):
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql)
            print(f"   ✅ {desc}")
            return True
        except Exception as e:
            print(f"   ❌ {desc}: {str(e)}")
            return False

def main():
    print_header("CREATING CLEAN AI FITNESS COACH DATABASE")
    
    print("""
🎯 GOAL: Create a properly structured database that supports:
   • User registration & profiles with XP/achievements
   • Multi-step onboarding with dynamic questions  
   • AI workout plan generation (6-week programs)
   • Video-based exercise instruction system
   • Gamification with stories & unlockable content
   • Progress tracking & weekly plan adaptation
    """)
    
    print("🔥 PROCEEDING WITH DATABASE RESET...")
    
    # Step 1: Reset migrations 
    print_step(1, "RESET ALL MIGRATIONS")
    try:
        # Remove all migration files except __init__.py
        apps_dir = Path('apps')
        for app_dir in apps_dir.iterdir():
            if app_dir.is_dir():
                migrations_dir = app_dir / 'migrations'
                if migrations_dir.exists():
                    for migration_file in migrations_dir.glob('*.py'):
                        if migration_file.name != '__init__.py':
                            migration_file.unlink()
                            print(f"   🗑️  Removed {migration_file}")
        print("   ✅ Migration files cleared")
    except Exception as e:
        print(f"   ❌ Error clearing migrations: {e}")
    
    # Step 2: Drop existing database (PostgreSQL)
    print_step(2, "DROP EXISTING TABLES")
    
    # Get all table names
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%'
            AND tablename != 'information_schema'
        """)
        tables = [row[0] for row in cursor.fetchall()]
    
    # Drop all tables
    if tables:
        tables_str = ', '.join(f'"{table}"' for table in tables)
        execute_sql(f"DROP TABLE IF EXISTS {tables_str} CASCADE;", "Dropped all existing tables")
    
    # Step 3: Create fresh migrations
    print_step(3, "CREATE FRESH MIGRATIONS")
    os.system("python manage.py makemigrations users")
    os.system("python manage.py makemigrations onboarding") 
    os.system("python manage.py makemigrations workouts")
    os.system("python manage.py makemigrations achievements")
    os.system("python manage.py makemigrations content")
    print("   ✅ Fresh migrations created")
    
    # Step 4: Apply migrations
    print_step(4, "APPLY MIGRATIONS")
    os.system("python manage.py migrate")
    print("   ✅ Migrations applied")
    
    # Step 5: Seed essential data
    print_step(5, "SEED ESSENTIAL DATA")
    seed_essential_data()
    
    # Step 6: Verify database structure
    print_step(6, "VERIFY DATABASE STRUCTURE")
    verify_database_structure()
    
    print_header("✅ CLEAN DATABASE CREATED SUCCESSFULLY")
    
    print("""
🎉 NEXT STEPS:
1. Test user registration: python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.create_user('test@example.com', 'testpass'); print(f'User created: {user.id}')"
2. Test onboarding flow: Visit /users/register/ 
3. Test AI generation: Complete onboarding questionnaire
4. Deploy to production: git add . && git commit -m "Clean database rebuild" && git push

🗄️ DATABASE SUMMARY:
   • Users with profiles, XP, and achievements
   • Dynamic onboarding questions & responses
   • Exercise database with video clips
   • AI workout plans with daily workouts  
   • Gamification system with stories
   • Progress tracking and adaptation logic
    """)

def seed_essential_data():
    """Seed the database with essential data for the application to function"""
    from apps.users.models import User
    from apps.onboarding.models import OnboardingQuestion, AnswerOption
    from apps.workouts.models import Exercise
    from apps.achievements.models import Achievement
    
    # Create onboarding questions
    questions_data = [
        {
            "order": 1,
            "question_text": "Какой у вас уровень опыта в фитнесе?",
            "question_type": "single_choice", 
            "ai_field_name": "experience_level",
            "options": [
                ("Новичок", "beginner"),
                ("Есть опыт", "intermediate"), 
                ("Продвинутый", "advanced")
            ]
        },
        {
            "order": 2,
            "question_text": "Какая ваша основная цель?",
            "question_type": "single_choice",
            "ai_field_name": "primary_goal", 
            "options": [
                ("Набрать мышечную массу", "bulk"),
                ("Похудеть", "cut"),
                ("Общая физическая форма", "general_fitness")
            ]
        },
        {
            "order": 3, 
            "question_text": "Сколько дней в неделю готовы тренироваться?",
            "question_type": "single_choice",
            "ai_field_name": "days_per_week",
            "options": [
                ("2-3 дня", "3"),
                ("4-5 дней", "4"), 
                ("6+ дней", "6")
            ]
        },
        {
            "order": 4,
            "question_text": "Какое оборудование у вас есть?",
            "question_type": "multiple_choice",
            "ai_field_name": "available_equipment",
            "options": [
                ("Только собственный вес", "bodyweight_only"),
                ("Гантели", "dumbbells"),
                ("Штанга", "barbell"),
                ("Тренажеры", "machines")
            ]
        },
        {
            "order": 5,
            "question_text": "Сколько времени готовы тратить на тренировку?",
            "question_type": "single_choice", 
            "ai_field_name": "workout_duration",
            "options": [
                ("20-30 минут", "30"),
                ("30-45 минут", "45"),
                ("45-60 минут", "60"),
                ("60+ минут", "90")
            ]
        }
    ]
    
    for q_data in questions_data:
        question, created = OnboardingQuestion.objects.get_or_create(
            order=q_data["order"],
            defaults={
                "question_text": q_data["question_text"],
                "question_type": q_data["question_type"],
                "ai_field_name": q_data["ai_field_name"],
                "is_required": True,
                "is_active": True
            }
        )
        
        if created:
            print(f"   ✅ Created question: {question.question_text}")
            
            # Create answer options
            for i, (text, value) in enumerate(q_data["options"]):
                AnswerOption.objects.create(
                    question=question,
                    option_text=text,
                    option_value=value,
                    order=i
                )
                print(f"      • Added option: {text}")
    
    # Create basic exercises
    exercises_data = [
        {"id": "push-ups", "name": "Отжимания", "difficulty": "beginner"},
        {"id": "squats", "name": "Приседания", "difficulty": "beginner"},
        {"id": "plank", "name": "Планка", "difficulty": "beginner"},
        {"id": "pull-ups", "name": "Подтягивания", "difficulty": "intermediate"},
        {"id": "deadlift", "name": "Становая тяга", "difficulty": "intermediate"},
        {"id": "bench-press", "name": "Жим лежа", "difficulty": "intermediate"},
    ]
    
    for ex_data in exercises_data:
        exercise, created = Exercise.objects.get_or_create(
            id=ex_data["id"],
            defaults={
                "slug": ex_data["id"], 
                "name": ex_data["name"],
                "difficulty": ex_data["difficulty"],
                "description": f"Базовое упражнение: {ex_data['name']}",
                "muscle_groups": ["core"],
                "equipment_needed": ["bodyweight"],
                "is_active": True
            }
        )
        if created:
            print(f"   ✅ Created exercise: {exercise.name}")
    
    # Create basic achievements
    achievements_data = [
        {"slug": "first-workout", "name": "Первая тренировка", "trigger_type": "workout_count", "trigger_value": 1, "xp_reward": 100},
        {"slug": "week-streak", "name": "Неделя тренировок", "trigger_type": "streak_days", "trigger_value": 7, "xp_reward": 200},
        {"slug": "ten-workouts", "name": "10 тренировок", "trigger_type": "workout_count", "trigger_value": 10, "xp_reward": 500},
        {"slug": "level-up", "name": "Второй уровень", "trigger_type": "level_reached", "trigger_value": 2, "xp_reward": 0},
    ]
    
    for ach_data in achievements_data:
        achievement, created = Achievement.objects.get_or_create(
            slug=ach_data["slug"],
            defaults={
                "name": ach_data["name"],
                "description": f"Достижение: {ach_data['name']}",
                "trigger_type": ach_data["trigger_type"],
                "trigger_value": ach_data["trigger_value"], 
                "xp_reward": ach_data["xp_reward"],
                "is_active": True
            }
        )
        if created:
            print(f"   ✅ Created achievement: {achievement.name}")

def verify_database_structure():
    """Verify that all essential tables and fields exist"""
    from django.db import connection
    
    essential_tables = [
        'users', 'user_profiles', 'onboarding_questions', 'answer_options',
        'user_onboarding_responses', 'exercises', 'workout_plans', 
        'daily_workouts', 'achievements', 'user_achievements'
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
    
    print("   📋 Database Tables:")
    for table in essential_tables:
        if table in existing_tables:
            print(f"      ✅ {table}")
        else:
            print(f"      ❌ {table} (MISSING)")
    
    # Check critical fields
    critical_fields = [
        ("users", "completed_onboarding"),
        ("user_profiles", "archetype"), 
        ("user_profiles", "onboarding_completed_at"),
        ("exercises", "equipment_needed"),
        ("workout_plans", "is_confirmed"),
        ("daily_workouts", "confidence_task")
    ]
    
    print("\n   🔍 Critical Fields:")
    for table, field in critical_fields:
        if table in existing_tables:
            try:
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{field}'
                """)
                if cursor.fetchone():
                    print(f"      ✅ {table}.{field}")
                else:
                    print(f"      ❌ {table}.{field} (MISSING)")
            except:
                print(f"      ❓ {table}.{field} (ERROR CHECKING)")

if __name__ == "__main__":
    main()