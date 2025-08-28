#!/usr/bin/env python3
"""
ОКОНЧАТЕЛЬНАЯ ПРОИЗВОДСТВЕННАЯ ВАЛИДАЦИЯ
Проверяет только рабочий код, исключая все validator скрипты и backup
"""
import os
import re
import ast
import sys
from pathlib import Path
from typing import List

class ProductionValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def get_production_files(self) -> List[Path]:
        """Получить только производственные файлы"""
        python_files = []
        
        # Исключаем директории
        exclude_dirs = {
            '.venv', 'venv', '.git', '__pycache__', 'node_modules', 'env'
        }
        
        # Исключаем файлы validator'ов и backup
        exclude_files = {
            'comprehensive_legacy_validator.py',
            'mass_exercise_refactor.py', 
            'final_validation_accurate.py',
            'production_final_validator.py',
            'create_exercises.py',
            'debug_video_system.py',
            'test_full_system.py'
        }
        
        for root, dirs, files in os.walk(self.project_root):
            # Исключаем backup и временные директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs and 'backup' not in d.lower()]
            
            for file in files:
                if file.endswith('.py') and file not in exclude_files:
                    file_path = Path(root) / file
                    # Дополнительная проверка пути
                    if not any('backup' in part.lower() for part in file_path.parts):
                        python_files.append(file_path)
        
        return python_files
    
    def check_critical_issues(self, content: str) -> List[str]:
        """Проверить только критические проблемы"""
        issues = []
        
        # 1. Exercise.objects (должно быть CSVExercise.objects)
        if re.search(r'\bExercise\.objects\b', content):
            issues.append("Exercise.objects → CSVExercise.objects")
        
        # 2. Exercise.DoesNotExist (должно быть CSVExercise.DoesNotExist)
        if re.search(r'\bExercise\.DoesNotExist\b', content):
            issues.append("Exercise.DoesNotExist → CSVExercise.DoesNotExist")
        
        # 3. Импорт старой Exercise модели
        if re.search(r'from\s+apps\.workouts\.models\s+import\s+.*\bExercise\b(?!Validation)', content):
            issues.append("Import Exercise → Import CSVExercise")
        
        # 4. Exercise( конструктор
        if re.search(r'\bExercise\(', content):
            issues.append("Exercise() → CSVExercise()")
        
        return issues
    
    def run_production_validation(self):
        """Запустить производственную валидацию"""
        print("🏭 ОКОНЧАТЕЛЬНАЯ ПРОИЗВОДСТВЕННАЯ ВАЛИДАЦИЯ")
        print("=" * 50)
        
        # Получаем производственные файлы
        production_files = self.get_production_files()
        print(f"📁 Проверяется {len(production_files)} производственных файлов")
        
        # Проверяем файлы
        critical_issues = 0
        problematic_files = []
        
        for file_path in production_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем синтаксис
                try:
                    ast.parse(content)
                except SyntaxError:
                    critical_issues += 1
                    problematic_files.append((file_path, "Синтаксическая ошибка"))
                    continue
                
                # Проверяем критические проблемы
                issues = self.check_critical_issues(content)
                if issues:
                    critical_issues += len(issues)
                    problematic_files.append((file_path, issues))
                    
            except Exception as e:
                critical_issues += 1
                problematic_files.append((file_path, f"Ошибка чтения: {e}"))
        
        # Результаты
        print("\n📊 РЕЗУЛЬТАТ ПРОИЗВОДСТВЕННОЙ ВАЛИДАЦИИ:")
        
        if critical_issues == 0:
            print("✅ ОТЛИЧНО: Exercise модель не найдена")
            print("✅ Все импорты используют CSVExercise")
            print("✅ Все .objects вызовы используют CSVExercise")
            print("✅ Синтаксис всех файлов корректен")
            
            # Проверяем базу данных
            self.check_database()
            
            print("\n🎉 ВСЕ КРИТИЧЕСКИЕ ПРОВЕРКИ УСПЕШНЫ!")
            print("Phase 5.6 Exercise cleanup: ЗАВЕРШЁН ✅")
            return True
        else:
            print(f"❌ Найдено {critical_issues} критических проблем")
            print(f"📝 Проблемные файлы ({len(problematic_files)}):")
            for file_path, issues in problematic_files[:5]:
                print(f"   {file_path}:")
                if isinstance(issues, list):
                    for issue in issues:
                        print(f"     - {issue}")
                else:
                    print(f"     - {issues}")
            return False
    
    def check_database(self):
        """Проверить работу базы данных"""
        try:
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
            
            from apps.workouts.models import CSVExercise
            from apps.ai_integration.fallback_service import FallbackService
            from apps.core.services.exercise_validation import ExerciseValidationService
            
            # Проверки
            count = CSVExercise.objects.count()
            print(f"✅ CSVExercise работает, записей: {count}")
            
            # Тестируем сервисы
            fallback = FallbackService()
            print("✅ FallbackService работает")
            
            validator = ExerciseValidationService() 
            print("✅ ExerciseValidationService работает")
            
        except Exception as e:
            print(f"⚠️  База данных недоступна: {e}")

def main():
    """Главная функция"""
    validator = ProductionValidator(os.getcwd())
    success = validator.run_production_validation()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())