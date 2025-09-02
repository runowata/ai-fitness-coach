#!/usr/bin/env python3
"""
STATIC SYSTEM VALIDATOR 
Находит ВСЕ критические ошибки через статический анализ кода
Работает без доступа к базе данных
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from collections import defaultdict


class StaticSystemValidator:
    """Статический валидатор кода без запуска Django"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.project_root = Path.cwd()
        
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
        """Проверка валидаторов в моделях"""
        print("🔍 Checking model validators...")
        
        # Находим WorkoutPlan model
        workout_plan_file = self.project_root / 'apps/workouts/models.py'
        if workout_plan_file.exists():
            with open(workout_plan_file, 'r') as f:
                content = f.read()
                
            # Ищем MinValueValidator для duration_weeks
            if 'duration_weeks' in content:
                match = re.search(
                    r'duration_weeks\s*=.*?validators\s*=\s*\[(.*?)\]',
                    content,
                    re.DOTALL
                )
                if match:
                    validators = match.group(1)
                    if 'MinValueValidator(4)' in validators or 'MinValueValidator( 4 )' in validators:
                        self.add_error(
                            "MODEL_VALIDATOR",
                            "WorkoutPlan.duration_weeks has MinValueValidator(4) but demo plan uses duration_weeks=1",
                            "apps/workouts/models.py:duration_weeks"
                        )
                        
        # Проверяем использование duration_weeks=1
        onboarding_views = self.project_root / 'apps/onboarding/views.py'
        if onboarding_views.exists():
            with open(onboarding_views, 'r') as f:
                content = f.read()
                
            if 'duration_weeks=1' in content or 'duration_weeks = 1' in content:
                self.add_info("MODEL_VALIDATOR", "Found duration_weeks=1 usage in onboarding")
                
    def check_model_fields_usage(self):
        """Проверка использования несуществующих полей моделей"""
        print("🔍 Checking model field usage...")
        
        # Анализируем модель WorkoutPlan
        workout_models_file = self.project_root / 'apps/workouts/models.py'
        if workout_models_file.exists():
            with open(workout_models_file, 'r') as f:
                model_content = f.read()
                
            # Извлекаем поля из модели WorkoutPlan
            workout_plan_match = re.search(
                r'class WorkoutPlan\(.*?\):(.*?)(?=\nclass|\Z)',
                model_content,
                re.DOTALL
            )
            
            if workout_plan_match:
                model_body = workout_plan_match.group(1)
                
                # Находим все определенные поля
                defined_fields = set()
                field_pattern = r'(\w+)\s*=\s*models\.'
                for match in re.finditer(field_pattern, model_body):
                    defined_fields.add(match.group(1))
                    
                # Проверяем использование полей в коде
                ai_services = self.project_root / 'apps/ai_integration/services.py'
                if ai_services.exists():
                    with open(ai_services, 'r') as f:
                        services_content = f.read()
                        
                    # Проверяем поля используемые в WorkoutPlan.objects.create
                    create_calls = re.findall(
                        r'WorkoutPlan\.objects\.create\((.*?)\)',
                        services_content,
                        re.DOTALL
                    )
                    
                    for create_call in create_calls:
                        # Извлекаем используемые поля
                        used_fields = re.findall(r'(\w+)\s*=', create_call)
                        
                        for field in used_fields:
                            if field not in defined_fields and field not in ['user', 'name']:
                                self.add_error(
                                    "MODEL_FIELD",
                                    f"WorkoutPlan.objects.create() uses non-existent field '{field}'",
                                    "apps/ai_integration/services.py"
                                )
                                
    # ========== VIEW SECURITY ==========
    
    def check_view_security(self):
        """Проверка безопасности views"""
        print("🔍 Checking view security...")
        
        views_file = self.project_root / 'apps/workouts/views.py'
        if views_file.exists():
            with open(views_file, 'r') as f:
                content = f.read()
                
            # Находим все функции с DailyWorkout
            functions = re.findall(
                r'def\s+(\w+)\(request[^)]*\):(.*?)(?=\ndef|\Z)',
                content,
                re.DOTALL
            )
            
            for func_name, func_body in functions:
                if 'DailyWorkout' in func_body and 'get_object_or_404' in func_body:
                    # Проверяем защиту через plan__user
                    if 'plan__user=request.user' not in func_body:
                        self.add_warning(
                            "VIEW_SECURITY", 
                            f"View '{func_name}' may allow access to other users' workouts",
                            f"apps/workouts/views.py:{func_name}"
                        )
                        
        # Проверяем media_proxy
        content_views = self.project_root / 'apps/content/views.py'
        if content_views.exists():
            with open(content_views, 'r') as f:
                content = f.read()
                
            # Ищем небезопасный fallback
            if 'if r2_public_url and not all([bucket' in content:
                if 'return HttpResponseRedirect(direct_url)' in content:
                    self.add_error(
                        "SECURITY",
                        "media_proxy exposes direct URLs without authentication in fallback mode",
                        "apps/content/views.py:media_proxy"
                    )
                    
    # ========== TEMPLATE VALIDATION ==========
    
    def check_template_variables(self):
        """Проверка переменных в шаблонах"""
        print("🔍 Checking template variables...")
        
        # Проверяем workout_day.html
        template_file = self.project_root / 'templates/workouts/workout_day.html'
        if template_file.exists():
            with open(template_file, 'r') as f:
                template_content = f.read()
                
            # Извлекаем используемые переменные
            used_vars = set()
            
            # Django переменные {{ var }}
            for match in re.finditer(r'{{\s*(\w+)', template_content):
                used_vars.add(match.group(1))
                
            # Переменные в for loops
            for match in re.finditer(r'{%\s*for\s+\w+\s+in\s+(\w+)', template_content):
                used_vars.add(match.group(1))
                
            # Теперь проверяем view
            views_file = self.project_root / 'apps/workouts/views.py'
            if views_file.exists():
                with open(views_file, 'r') as f:
                    views_content = f.read()
                    
                # Находим workout_day view
                view_match = re.search(
                    r'def\s+workout_day\(.*?\):(.*?)(?=\ndef|\Z)',
                    views_content,
                    re.DOTALL
                )
                
                if view_match:
                    view_body = view_match.group(1)
                    
                    # Ищем render вызов
                    render_match = re.search(
                        r'render\([^,]+,\s*[\'"].*?workout_day\.html[\'"][^}]+({[^}]+})',
                        view_body
                    )
                    
                    if render_match:
                        context = render_match.group(1)
                        
                        # Проверяем каждую переменную
                        for var in used_vars:
                            if var not in ['block', 'extends', 'load', 'static', 'url', 'if', 'else', 'endif', 'for', 'endfor']:
                                if f'"{var}"' not in context and f"'{var}'" not in context:
                                    self.add_warning(
                                        "TEMPLATE_VAR",
                                        f"Template uses variable '{var}' but view might not provide it",
                                        "templates/workouts/workout_day.html"
                                    )
                                    
    # ========== EDGE CASES ==========
    
    def check_edge_cases(self):
        """Проверка edge cases в коде"""
        print("🔍 Checking edge cases...")
        
        # Проверяем random.sample
        for py_file in self.project_root.rglob('apps/**/*.py'):
            if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            with open(py_file, 'r') as f:
                content = f.read()
                
            # Находим random.sample вызовы
            samples = re.findall(
                r'random\.sample\(([^,]+),\s*k=(\d+)\)',
                content
            )
            
            for collection, k_value in samples:
                k = int(k_value)
                if k > 1:
                    # Проверяем есть ли проверка длины перед sample
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f'random.sample({collection}' in line:
                            # Проверяем предыдущие 5 строк на проверку длины
                            check_found = False
                            for j in range(max(0, i-5), i):
                                if f'len({collection})' in lines[j] or f'{collection}.count()' in lines[j]:
                                    check_found = True
                                    break
                                    
                            if not check_found:
                                self.add_error(
                                    "EDGE_CASE",
                                    f"random.sample(k={k}) without length check - will fail if collection < {k}",
                                    f"{py_file}:{i+1}"
                                )
                                
    # ========== ERROR HANDLING ==========
    
    def check_error_handling(self):
        """Проверка обработки ошибок"""
        print("🔍 Checking error handling...")
        
        critical_files = [
            'apps/onboarding/views.py',
            'apps/ai_integration/services.py',
            'apps/content/views.py',
        ]
        
        for file_path in critical_files:
            file = self.project_root / file_path
            if file.exists():
                with open(file, 'r') as f:
                    content = f.read()
                    
                # Находим функции
                functions = re.findall(
                    r'def\s+(\w+)\([^)]*\):(.*?)(?=\ndef|\Z)',
                    content,
                    re.DOTALL
                )
                
                for func_name, func_body in functions:
                    # Пропускаем приватные функции
                    if func_name.startswith('_'):
                        continue
                        
                    # Проверяем критические функции
                    critical_funcs = [
                        'create_demo_plan', 'generate_plan', 'media_proxy',
                        'complete_onboarding', 'daily_workout'
                    ]
                    
                    if any(cf in func_name for cf in critical_funcs):
                        if 'try:' not in func_body:
                            self.add_warning(
                                "ERROR_HANDLING",
                                f"Critical function '{func_name}' has no error handling",
                                f"{file_path}:{func_name}"
                            )
                            
                        if 'except' in func_body and 'logger' not in func_body and 'print' not in func_body:
                            self.add_warning(
                                "ERROR_HANDLING",
                                f"Function '{func_name}' catches exceptions but doesn't log them",
                                f"{file_path}:{func_name}"
                            )
                            
    # ========== MIGRATION CHECK ==========
    
    def check_migrations(self):
        """Проверка миграций"""
        print("🔍 Checking migrations...")
        
        # Проверяем наличие полей в миграциях
        migrations_dir = self.project_root / 'apps/workouts/migrations'
        
        if migrations_dir.exists():
            # Собираем все поля из миграций
            migration_fields = set()
            
            for migration_file in sorted(migrations_dir.glob('*.py')):
                if '__pycache__' in str(migration_file):
                    continue
                    
                with open(migration_file, 'r') as f:
                    content = f.read()
                    
                # Ищем AddField операции
                add_fields = re.findall(r"migrations\.AddField\(\s*model_name='workoutplan',\s*name='(\w+)'", content)
                migration_fields.update(add_fields)
                
                # Ищем поля в CreateModel
                if 'CreateModel' in content and "'workoutplan'" in content.lower():
                    create_fields = re.findall(r"\('(\w+)',\s*models\.", content)
                    migration_fields.update(create_fields)
                    
            # Проверяем что поля используемые в коде есть в миграциях
            required_fields = ['started_at', 'is_active', 'is_confirmed']
            for field in required_fields:
                if field not in migration_fields:
                    self.add_warning(
                        "MIGRATION",
                        f"Field 'WorkoutPlan.{field}' used in code but might not exist in migrations",
                        "apps/workouts/migrations/"
                    )
                    
    # ========== DATA DEPENDENCIES ==========
    
    def check_data_dependencies(self):
        """Проверка зависимостей от данных"""
        print("🔍 Checking data dependencies...")
        
        # Проверяем что код не падает если нет упражнений
        onboarding_file = self.project_root / 'apps/onboarding/views.py'
        if onboarding_file.exists():
            with open(onboarding_file, 'r') as f:
                content = f.read()
                
            # Находим create_demo_plan_for_user
            func_match = re.search(
                r'def\s+create_demo_plan_for_user\([^)]*\):(.*?)(?=\ndef|\Z)',
                content,
                re.DOTALL
            )
            
            if func_match:
                func_body = func_match.group(1)
                
                # Проверяем обработку пустого списка упражнений
                if 'random.sample(exercises, k=' in func_body:
                    if 'if not available_exercises.exists()' in func_body:
                        # Проверяем что после fallback есть проверка длины
                        if 'len(exercises)' not in func_body and 'min(3, len(exercises))' not in func_body:
                            self.add_error(
                                "DATA_DEPENDENCY",
                                "Demo plan will crash if less than 3 exercises available",
                                "apps/onboarding/views.py:create_demo_plan_for_user"
                            )
                            
    # ========== URL PATTERNS ==========
    
    def check_url_patterns(self):
        """Проверка URL паттернов"""
        print("🔍 Checking URL patterns...")
        
        # Проверяем content urls
        content_urls = self.project_root / 'apps/content/urls.py'
        if content_urls.exists():
            with open(content_urls, 'r') as f:
                content = f.read()
                
            # Проверяем media_proxy URL
            if 'media_proxy' in content:
                if 'path("media/<path:key>"' in content:
                    self.add_info("URL_PATTERN", "media_proxy URL pattern looks correct")
                else:
                    self.add_warning(
                        "URL_PATTERN",
                        "media_proxy URL pattern might be incorrect",
                        "apps/content/urls.py"
                    )
                    
    # ========== MAIN VALIDATION ==========
    
    def validate_all(self) -> Dict[str, Any]:
        """Запустить полную валидацию"""
        print("\n" + "="*60)
        print("🚀 STATIC SYSTEM VALIDATION")
        print("="*60 + "\n")
        
        # Model checks
        self.check_model_validators()
        self.check_model_fields_usage()
        
        # Security checks
        self.check_view_security()
        
        # Template checks
        self.check_template_variables()
        
        # Code quality
        self.check_edge_cases()
        self.check_error_handling()
        
        # Migrations
        self.check_migrations()
        
        # Data dependencies
        self.check_data_dependencies()
        
        # URLs
        self.check_url_patterns()
        
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
        
    def print_report(self, results: Dict[str, Any]) -> bool:
        """Красивый вывод отчета"""
        print("\n" + "="*60)
        print("📊 VALIDATION REPORT")
        print("="*60)
        
        # Errors
        if results['errors']:
            print(f"\n❌ CRITICAL ERRORS: {len(results['errors'])}")
            print("-"*40)
            for error in results['errors']:
                print(f"  [{error['category']}]")
                print(f"     {error['message']}")
                if error['location']:
                    print(f"     📍 {error['location']}")
                print()
                
        # Warnings
        if results['warnings']:
            print(f"\n⚠️  WARNINGS: {len(results['warnings'])}")
            print("-"*40)
            for warning in results['warnings']:
                print(f"  [{warning['category']}]")
                print(f"     {warning['message']}")
                if warning['location']:
                    print(f"     📍 {warning['location']}")
                print()
                
        # Info
        if results['info']:
            print(f"\nℹ️  INFO: {len(results['info'])}")
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
    validator = StaticSystemValidator()
    results = validator.validate_all()
    success = validator.print_report(results)
    
    # Сохранить отчет
    with open('static_validation_report.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("📄 Full report saved to static_validation_report.json")
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())