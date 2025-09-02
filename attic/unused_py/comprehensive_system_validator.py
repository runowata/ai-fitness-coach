#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM VALIDATOR
Находит ВСЕ критические ошибки за один проход
Проверяет модели, views, flows, данные, permissions
"""

import os
import sys
import json
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Any
from collections import defaultdict

# Try Django setup but continue if DB is unavailable
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Django setup failed (DB unavailable?): {e}")
    DJANGO_AVAILABLE = False

from django.core.exceptions import ValidationError
from django.db import models
from django.apps import apps
from django.core.validators import MinValueValidator, MaxValueValidator


class SystemValidator:
    """Комплексный валидатор всей системы"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def add_error(self, category: str, message: str, location: str = ""):
        """Добавить критическую ошибку"""
        self.errors.append({
            "level": "ERROR",
            "category": category,
            "message": message,
            "location": location
        })
        
    def add_warning(self, category: str, message: str, location: str = ""):
        """Добавить предупреждение"""
        self.warnings.append({
            "level": "WARNING", 
            "category": category,
            "message": message,
            "location": location
        })
        
    def add_info(self, category: str, message: str):
        """Добавить информационное сообщение"""
        self.info.append({
            "level": "INFO",
            "category": category,
            "message": message
        })
        
    # ========== MODEL VALIDATION ==========
    
    def check_model_validators(self):
        """Проверка всех валидаторов моделей на конфликты"""
        print("🔍 Checking model validators...")
        
        # Проверяем WorkoutPlan
        WorkoutPlan = apps.get_model('workouts', 'WorkoutPlan')
        for field in WorkoutPlan._meta.fields:
            if field.name == 'duration_weeks':
                validators = field.validators
                min_val = None
                max_val = None
                
                for v in validators:
                    if isinstance(v, MinValueValidator):
                        min_val = v.limit_value
                    elif isinstance(v, MaxValueValidator):
                        max_val = v.limit_value
                        
                if min_val and min_val > 1:
                    self.add_error(
                        "MODEL_VALIDATOR",
                        f"WorkoutPlan.duration_weeks has MinValueValidator({min_val}) but demo plan uses duration_weeks=1",
                        "apps/workouts/models.py"
                    )
                    
        self.add_info("MODEL_VALIDATOR", f"Checked {len(apps.get_models())} models")
        
    def check_model_fields_exist(self):
        """Проверка что все используемые поля существуют в моделях"""
        print("🔍 Checking model field existence...")
        
        # Словарь полей которые используются в коде
        field_usage = {
            'WorkoutPlan': ['started_at', 'is_active', 'is_confirmed', 'status', 'plan_data', 'name'],
            'DailyWorkout': ['exercises', 'playlist_items', 'day_number', 'week_number'],
            'CSVExercise': ['id', 'name_ru', 'level', 'is_active'],
            'MediaAsset': ['exercise', 'file_url', 'category', 'is_active'],
            'DailyPlaylistItem': ['day', 'order', 'media', 'role']
        }
        
        for model_name, expected_fields in field_usage.items():
            try:
                if '.' not in model_name:
                    # Определяем app name
                    if model_name in ['WorkoutPlan', 'DailyWorkout', 'CSVExercise', 'DailyPlaylistItem']:
                        app_label = 'workouts'
                    elif model_name in ['MediaAsset']:
                        app_label = 'content'
                    else:
                        continue
                        
                    model = apps.get_model(app_label, model_name)
                else:
                    app_label, model_name = model_name.split('.')
                    model = apps.get_model(app_label, model_name)
                    
                actual_fields = [f.name for f in model._meta.fields]
                actual_fields.extend([f.name for f in model._meta.many_to_many])
                
                # Проверка related_name для обратных связей
                for rel in model._meta.related_objects:
                    if rel.related_name:
                        actual_fields.append(rel.related_name)
                
                for field in expected_fields:
                    if field not in actual_fields:
                        # Проверяем есть ли это поле как property или method
                        if not hasattr(model, field):
                            self.add_error(
                                "MODEL_FIELD",
                                f"Model {model_name} missing field '{field}' that is used in code",
                                f"{app_label}/models.py"
                            )
                            
            except LookupError as e:
                self.add_error(
                    "MODEL_FIELD",
                    f"Model {model_name} not found: {e}",
                    ""
                )
                
    # ========== VIEW VALIDATION ==========
    
    def check_view_permissions(self):
        """Проверка прав доступа во views"""
        print("🔍 Checking view permissions...")
        
        views_dir = Path('apps/workouts/views.py')
        if views_dir.exists():
            with open(views_dir, 'r') as f:
                content = f.read()
                
            # Проверка что все views с DailyWorkout проверяют plan__user
            daily_workout_views = re.findall(
                r'def\s+(\w+)\(request.*?\):[^}]+?DailyWorkout[^}]+?get_object_or_404',
                content,
                re.DOTALL
            )
            
            for view_name in daily_workout_views:
                # Найти конкретный view
                view_match = re.search(
                    rf'def\s+{view_name}\(request.*?\):(.*?)(?=\ndef|\Z)',
                    content,
                    re.DOTALL
                )
                if view_match:
                    view_body = view_match.group(1)
                    if 'plan__user=request.user' not in view_body:
                        self.add_warning(
                            "VIEW_PERMISSION",
                            f"View '{view_name}' accesses DailyWorkout without plan__user check",
                            f"apps/workouts/views.py:{view_name}"
                        )
                        
        # Проверка media_proxy на безопасность
        content_views = Path('apps/content/views.py')
        if content_views.exists():
            with open(content_views, 'r') as f:
                content = f.read()
                
            if 'return HttpResponseRedirect(direct_url)' in content:
                if 'if r2_public_url and not all([bucket' in content:
                    self.add_error(
                        "SECURITY",
                        "media_proxy has unsafe fallback that exposes direct URLs without auth",
                        "apps/content/views.py:media_proxy"
                    )
                    
    def check_template_variables(self):
        """Проверка что все переменные в шаблонах передаются из views"""
        print("🔍 Checking template variables...")
        
        templates_to_check = {
            'templates/workouts/workout_day.html': ['day', 'playlist', 'exercises'],
            'templates/workouts/daily_workout.html': ['workout', 'video_playlist'],
        }
        
        for template_path, required_vars in templates_to_check.items():
            template_file = Path(template_path)
            if template_file.exists():
                with open(template_file, 'r') as f:
                    template_content = f.read()
                    
                for var in required_vars:
                    # Проверяем использование переменной в шаблоне
                    if f'{{{{ {var}' in template_content or f'{{% for' in template_content and var in template_content:
                        # Находим view который рендерит этот шаблон
                        template_name = template_path.split('/')[-1]
                        
                        # Ищем в views.py
                        views_files = list(Path('apps').rglob('views.py'))
                        for view_file in views_files:
                            with open(view_file, 'r') as vf:
                                view_content = vf.read()
                                
                            # Находим render с этим шаблоном
                            renders = re.findall(
                                rf'render\([^,]+,\s*[\'"].*?{template_name}[\'"][^)]+\)',
                                view_content
                            )
                            
                            for render_call in renders:
                                if f"'{var}'" not in render_call and f'"{var}"' not in render_call:
                                    self.add_warning(
                                        "TEMPLATE_VAR",
                                        f"Template uses '{var}' but view might not pass it",
                                        f"{template_path}"
                                    )
                                    
    # ========== FLOW VALIDATION ==========
    
    def simulate_user_registration(self):
        """Симуляция процесса регистрации пользователя"""
        print("🔍 Simulating user registration flow...")
        
        try:
            from django.contrib.auth import get_user_model
            from apps.users.models import UserProfile
            
            User = get_user_model()
            
            # Проверяем что UserProfile создается через сигнал
            test_username = "validator_test_user_12345"
            
            # Cleanup если был предыдущий тест
            User.objects.filter(username=test_username).delete()
            
            # Создаем пользователя
            user = User.objects.create_user(
                username=test_username,
                email=f"{test_username}@test.com",
                password="TestPass123!"
            )
            
            # Проверяем создался ли UserProfile
            if not hasattr(user, 'profile'):
                self.add_error(
                    "USER_FLOW",
                    "UserProfile not created automatically via signal",
                    "apps/users/signals.py"
                )
            else:
                self.add_info("USER_FLOW", "User registration flow OK")
                
            # Cleanup
            user.delete()
            
        except Exception as e:
            self.add_error(
                "USER_FLOW",
                f"User registration simulation failed: {e}",
                ""
            )
            
    def simulate_onboarding_flow(self):
        """Симуляция процесса онбординга"""
        print("🔍 Simulating onboarding flow...")
        
        try:
            from apps.onboarding.models import OnboardingData
            from apps.workouts.models import WorkoutPlan, CSVExercise
            
            # Проверяем что есть хотя бы минимум упражнений
            exercise_count = CSVExercise.objects.filter(is_active=True).count()
            if exercise_count < 3:
                self.add_error(
                    "ONBOARDING_FLOW",
                    f"Only {exercise_count} exercises available, need at least 3 for demo plan",
                    "data/exercises"
                )
                
            # Проверяем создание демо плана
            test_plan_data = {
                "demo": True,
                "exercises_count": 3
            }
            
            # Проверяем валидаторы
            duration_weeks_field = WorkoutPlan._meta.get_field('duration_weeks')
            for validator in duration_weeks_field.validators:
                if isinstance(validator, MinValueValidator):
                    if validator.limit_value > 1:
                        self.add_error(
                            "ONBOARDING_FLOW",
                            f"Cannot create demo plan with duration_weeks=1 due to MinValueValidator({validator.limit_value})",
                            "apps/workouts/models.py:WorkoutPlan"
                        )
                        
        except Exception as e:
            self.add_error(
                "ONBOARDING_FLOW",
                f"Onboarding simulation failed: {e}",
                ""
            )
            
    def simulate_workout_creation(self):
        """Симуляция создания тренировки с плейлистом"""
        print("🔍 Simulating workout creation flow...")
        
        try:
            from apps.workouts.models import DailyPlaylistItem
            from apps.content.models import MediaAsset
            
            # Проверяем наличие медиа файлов
            media_count = MediaAsset.objects.filter(is_active=True).count()
            if media_count == 0:
                self.add_warning(
                    "WORKOUT_FLOW",
                    "No MediaAssets available for playlist creation",
                    "apps/content/models.py"
                )
                
            # Проверяем категории медиа
            required_categories = ['intro', 'warmup', 'exercise_technique', 'cooldown']
            for category in required_categories:
                count = MediaAsset.objects.filter(category=category, is_active=True).count()
                if count == 0:
                    self.add_warning(
                        "WORKOUT_FLOW",
                        f"No MediaAssets with category '{category}' for playlist",
                        "data/media"
                    )
                    
        except Exception as e:
            self.add_error(
                "WORKOUT_FLOW",
                f"Workout creation simulation failed: {e}",
                ""
            )
            
    # ========== DATA VALIDATION ==========
    
    def check_minimum_data_requirements(self):
        """Проверка минимальных требований к данным"""
        print("🔍 Checking minimum data requirements...")
        
        requirements = {
            'CSVExercise': {
                'model': 'workouts.CSVExercise',
                'filters': {'is_active': True},
                'minimum': 3,
                'error_msg': "Need at least 3 active exercises for demo plan"
            },
            'MediaAsset': {
                'model': 'content.MediaAsset',
                'filters': {'is_active': True},
                'minimum': 1,
                'error_msg': "Need at least 1 media asset for playlists"
            },
            'OnboardingQuestion': {
                'model': 'onboarding.OnboardingQuestion',
                'filters': {'is_active': True},
                'minimum': 1,
                'error_msg': "Need at least 1 onboarding question"
            }
        }
        
        for name, req in requirements.items():
            try:
                app_label, model_name = req['model'].split('.')
                model = apps.get_model(app_label, model_name)
                count = model.objects.filter(**req['filters']).count()
                
                if count < req['minimum']:
                    self.add_error(
                        "DATA_REQUIREMENTS",
                        f"{req['error_msg']} (found: {count})",
                        f"{req['model']}"
                    )
                else:
                    self.add_info(
                        "DATA_REQUIREMENTS",
                        f"{name}: {count} records found ✓"
                    )
                    
            except Exception as e:
                self.add_warning(
                    "DATA_REQUIREMENTS",
                    f"Could not check {name}: {e}",
                    ""
                )
                
    # ========== CODE QUALITY ==========
    
    def check_error_handling(self):
        """Проверка обработки ошибок в критических местах"""
        print("🔍 Checking error handling...")
        
        critical_functions = [
            ('apps/onboarding/views.py', 'create_demo_plan_for_user'),
            ('apps/ai_integration/services.py', 'generate_plan'),
            ('apps/content/views.py', 'media_proxy'),
        ]
        
        for file_path, function_name in critical_functions:
            file = Path(file_path)
            if file.exists():
                with open(file, 'r') as f:
                    content = f.read()
                    
                # Находим функцию
                func_pattern = rf'def\s+{function_name}\([^)]*\):(.*?)(?=\ndef|\Z)'
                match = re.search(func_pattern, content, re.DOTALL)
                
                if match:
                    func_body = match.group(1)
                    
                    # Проверяем наличие try/except
                    if 'try:' not in func_body:
                        self.add_warning(
                            "ERROR_HANDLING",
                            f"Function '{function_name}' has no try/except blocks",
                            f"{file_path}:{function_name}"
                        )
                        
                    # Проверяем что exceptions логируются
                    if 'except' in func_body and 'logger' not in func_body:
                        self.add_warning(
                            "ERROR_HANDLING",
                            f"Function '{function_name}' catches exceptions but doesn't log them",
                            f"{file_path}:{function_name}"
                        )
                        
    def check_edge_cases(self):
        """Проверка edge cases"""
        print("🔍 Checking edge cases...")
        
        # Проверка random.sample
        files_to_check = list(Path('apps').rglob('*.py'))
        for file in files_to_check:
            with open(file, 'r') as f:
                content = f.read()
                
            # Находим все random.sample
            samples = re.findall(r'random\.sample\([^,]+,\s*k=(\d+)\)', content)
            for sample_k in samples:
                k_value = int(sample_k)
                if k_value > 1:
                    # Проверяем что есть проверка длины
                    if 'if len(' not in content and '.count()' not in content:
                        self.add_warning(
                            "EDGE_CASE",
                            f"random.sample with k={k_value} without length check",
                            str(file)
                        )
                        
    # ========== MIGRATIONS ==========
    
    def check_migrations(self):
        """Проверка консистентности миграций"""
        print("🔍 Checking migrations...")
        
        # Проверяем что все модели имеют миграции
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connection
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            self.add_error(
                "MIGRATIONS",
                f"Found {len(plan)} unapplied migrations",
                "Run: python manage.py migrate"
            )
        else:
            self.add_info("MIGRATIONS", "All migrations applied ✓")
            
    # ========== MAIN VALIDATION ==========
    
    def validate_all(self) -> Dict[str, Any]:
        """Запустить полную валидацию системы"""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE SYSTEM VALIDATION")
        print("="*60 + "\n")
        
        # Model checks
        self.check_model_validators()
        self.check_model_fields_exist()
        
        # View checks
        self.check_view_permissions()
        self.check_template_variables()
        
        # Flow simulation
        self.simulate_user_registration()
        self.simulate_onboarding_flow()
        self.simulate_workout_creation()
        
        # Data checks
        self.check_minimum_data_requirements()
        
        # Code quality
        self.check_error_handling()
        self.check_edge_cases()
        
        # Migrations
        self.check_migrations()
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "total_info": len(self.info)
            }
        }
        
    def print_report(self, results: Dict[str, Any]):
        """Красивый вывод отчета"""
        print("\n" + "="*60)
        print("📊 VALIDATION REPORT")
        print("="*60)
        
        # Errors
        if results['errors']:
            print("\n❌ CRITICAL ERRORS:", len(results['errors']))
            print("-"*40)
            for error in results['errors']:
                print(f"  [{error['category']}] {error['message']}")
                if error['location']:
                    print(f"     📍 Location: {error['location']}")
                print()
                
        # Warnings
        if results['warnings']:
            print("\n⚠️  WARNINGS:", len(results['warnings']))
            print("-"*40)
            for warning in results['warnings']:
                print(f"  [{warning['category']}] {warning['message']}")
                if warning['location']:
                    print(f"     📍 Location: {warning['location']}")
                print()
                
        # Info
        if results['info']:
            print("\nℹ️  INFO:", len(results['info']))
            print("-"*40)
            for info in results['info']:
                print(f"  [{info['category']}] {info['message']}")
                
        # Summary
        print("\n" + "="*60)
        print("📈 SUMMARY:")
        print("-"*40)
        
        if results['summary']['total_errors'] == 0:
            print("✅ NO CRITICAL ERRORS FOUND!")
            print("🎉 System is ready for deployment")
        else:
            print(f"❌ Found {results['summary']['total_errors']} CRITICAL ERRORS")
            print(f"⚠️  Found {results['summary']['total_warnings']} warnings")
            print("\n🔧 FIX ALL ERRORS BEFORE DEPLOYMENT!")
            
        print("="*60 + "\n")
        
        return results['summary']['total_errors'] == 0


def main():
    """Запустить валидацию"""
    validator = SystemValidator()
    results = validator.validate_all()
    success = validator.print_report(results)
    
    # Сохранить отчет в файл
    with open('validation_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("📄 Full report saved to validation_report.json")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())