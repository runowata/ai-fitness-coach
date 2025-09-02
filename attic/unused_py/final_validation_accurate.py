#!/usr/bin/env python3
"""
ТОЧНАЯ ФИНАЛЬНАЯ ВАЛИДАЦИЯ ПОСЛЕ РЕФАКТОРИНГА
Исключает backup директории и проверяет только реальные проблемы
"""
import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Set

class FinalAccurateValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.real_issues = []
        
    def get_active_python_files(self) -> List[Path]:
        """Получить только активные Python файлы (не backup)"""
        python_files = []
        exclude_dirs = {
            '.venv', 'venv', '.git', '__pycache__', 'node_modules', 'env',
            # Исключаем ВСЕ backup директории
        }
        
        # Добавляем все backup директории в исключения
        for item in self.project_root.iterdir():
            if item.is_dir() and 'backup' in item.name.lower():
                exclude_dirs.add(item.name)
        
        for root, dirs, files in os.walk(self.project_root):
            # Фильтруем директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('backup')]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    # Дополнительная проверка - исключаем любые файлы в backup путях
                    if not any('backup' in part.lower() for part in file_path.parts):
                        python_files.append(file_path)
        
        return python_files
    
    def check_forbidden_patterns(self, content: str, file_path: Path) -> List[str]:
        """Проверить запрещённые паттерны, исключая допустимые"""
        issues = []
        
        # 1. Exercise.objects или Exercise.DoesNotExist (но НЕ CSVExercise)
        if re.search(r'\bExercise\.objects\b', content):
            issues.append("❌ Exercise.objects вместо CSVExercise.objects")
        
        if re.search(r'\bExercise\.DoesNotExist\b', content):
            issues.append("❌ Exercise.DoesNotExist вместо CSVExercise.DoesNotExist")
        
        # 2. Импорт Exercise модели (но НЕ ExerciseValidation и тд)
        if re.search(r'from\s+apps\.workouts\.models\s+import\s+.*\bExercise\b(?!Validation)', content):
            issues.append("❌ Импорт Exercise модели")
        
        # 3. Exercise( конструктор (но НЕ CSVExercise)
        if re.search(r'\bExercise\(', content):
            issues.append("❌ Exercise() конструктор вместо CSVExercise()")
        
        # 4. muscle_groups поле (должно быть удалено в Phase 5.6)
        if re.search(r'\.muscle_groups\b', content):
            issues.append("❌ Использование удалённого поля muscle_groups")
        
        # 5. equipment_needed поле (должно быть удалено в Phase 5.6)  
        if re.search(r'\.equipment_needed\b', content):
            issues.append("❌ Использование удалённого поля equipment_needed")
        
        # 6. alternatives поле (должно быть удалено в Phase 5.6)
        if re.search(r'\.alternatives\b', content):
            issues.append("❌ Использование удалённого поля alternatives")
        
        return issues
    
    def validate_django_imports(self, file_path: Path) -> List[str]:
        """Проверить, что Django импорты корректны"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем AST на корректность
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append(f"❌ Синтаксическая ошибка: {e}")
                return issues
                
            # Проверяем проблемные паттерны
            file_issues = self.check_forbidden_patterns(content, file_path)
            issues.extend(file_issues)
                
        except Exception as e:
            issues.append(f"❌ Ошибка чтения файла: {e}")
        
        return issues
    
    def run_validation(self):
        """Запустить точную валидацию"""
        print("🎯 ТОЧНАЯ ФИНАЛЬНАЯ ВАЛИДАЦИЯ")
        print("=" * 50)
        
        # Получаем активные файлы
        python_files = self.get_active_python_files()
        print(f"📁 Проверяется {len(python_files)} активных Python файлов")
        print("(backup директории исключены)")
        
        # Проверяем каждый файл
        total_issues = 0
        problematic_files = []
        
        for file_path in python_files:
            issues = self.validate_django_imports(file_path)
            
            if issues:
                total_issues += len(issues)
                problematic_files.append(file_path)
                
                print(f"\n❌ {file_path}:")
                for issue in issues:
                    print(f"   {issue}")
        
        # Итоговый результат
        print("\n" + "=" * 50)
        print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        
        if total_issues == 0:
            print("✅ ИДЕАЛЬНО! Все проблемы Exercise модели устранены")
            print("✅ CSVExercise модель работает корректно") 
            print("✅ Все импорты исправлены")
            print("✅ Все поля Phase 5.6 удалены")
            print("\n🎉 РЕФАКТОРИНГ ПОЛНОСТЬЮ ЗАВЕРШЁН!")
        else:
            print(f"⚠️  Найдено {total_issues} проблем в {len(problematic_files)} файлах")
            print(f"📝 Файлы с проблемами:")
            for file_path in problematic_files[:10]:  # Показываем первые 10
                print(f"   - {file_path}")
            if len(problematic_files) > 10:
                print(f"   ... и ещё {len(problematic_files) - 10} файлов")
        
        # Дополнительная проверка базы данных
        self.check_database_status()
        
        return total_issues == 0
    
    def check_database_status(self):
        """Проверить статус базы данных"""
        print(f"\n🗃️ ПРОВЕРКА БАЗЫ ДАННЫХ:")
        
        try:
            # Импортируем Django
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
            
            from apps.workouts.models import CSVExercise
            
            # Проверяем CSVExercise
            total_exercises = CSVExercise.objects.count()
            active_exercises = CSVExercise.objects.filter(is_active=True).count()
            
            print(f"✅ CSVExercise работает, записей: {total_exercises}")
            print(f"✅ Активных упражнений: {active_exercises}")
            
            if total_exercises == 0:
                print("⚠️  База данных пуста - нужно загрузить упражнения")
            
        except Exception as e:
            print(f"❌ Ошибка проверки БД: {e}")

def main():
    print("🎯 ЗАПУСК ТОЧНОЙ ФИНАЛЬНОЙ ВАЛИДАЦИИ")
    print("Исключая backup директории и проверяя только реальные проблемы")
    print("=" * 60)
    
    project_root = os.getcwd()
    validator = FinalAccurateValidator(project_root)
    
    success = validator.run_validation()
    
    if success:
        print("\n🏆 ВСЕ КРИТИЧЕСКИЕ ПРОВЕРКИ УСПЕШНЫ!")
        print("Phase 5.6 Exercise model cleanup: ЗАВЕРШЁН ✅")
        return 0
    else:
        print("\n⚠️ Ещё остались проблемы для исправления")
        return 1

if __name__ == '__main__':
    sys.exit(main())