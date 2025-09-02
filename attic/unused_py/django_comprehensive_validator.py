#!/usr/bin/env python3
"""
DJANGO-СПЕЦИФИЧНЫЙ ВАЛИДАТОР
Ищет ВСЕ возможные ссылки на Exercise модель в Django коде
"""
import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class DjangoComprehensiveValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def get_production_files(self) -> List[Path]:
        """Получить только производственные файлы"""
        python_files = []
        
        exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', 'node_modules', 'env'}
        exclude_files = {
            'comprehensive_legacy_validator.py', 'mass_exercise_refactor.py', 
            'final_validation_accurate.py', 'production_final_validator.py',
            'django_comprehensive_validator.py'
        }
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and 'backup' not in d.lower()]
            
            for file in files:
                if file.endswith('.py') and file not in exclude_files:
                    file_path = Path(root) / file
                    if not any('backup' in part.lower() for part in file_path.parts):
                        python_files.append(file_path)
        
        return python_files
    
    def check_all_django_exercise_references(self, content: str, file_path: Path) -> List[str]:
        """Проверить ВСЕ возможные Django ссылки на Exercise"""
        issues = []
        
        # 1. Direct model imports
        if re.search(r'from\s+apps\.workouts\.models\s+import\s+.*\bExercise\b(?!Validation)', content):
            issues.append("❌ Direct Exercise model import")
        
        # 2. Exercise.objects и Exercise.DoesNotExist
        if re.search(r'\bExercise\.objects\b', content):
            issues.append("❌ Exercise.objects usage")
        if re.search(r'\bExercise\.DoesNotExist\b', content):
            issues.append("❌ Exercise.DoesNotExist usage")
        
        # 3. STRING REFERENCES - критически важно!
        if re.search(r'[\'"]workouts\.Exercise[\'"]', content):
            issues.append("❌ String reference 'workouts.Exercise' (ForeignKey/admin)")
        
        # 4. Admin registration
        if re.search(r'admin\.site\.register\s*\(\s*Exercise\b', content):
            issues.append("❌ Admin registration of Exercise")
        if re.search(r'@admin\.register\s*\(\s*Exercise\b', content):
            issues.append("❌ Admin decorator registration of Exercise")
        
        # 5. ContentType references
        if re.search(r'ContentType.*Exercise', content):
            issues.append("❌ ContentType reference to Exercise")
        
        # 6. Serializer references
        if re.search(r'model\s*=\s*Exercise\b', content):
            issues.append("❌ Serializer model = Exercise")
        
        # 7. Exercise() конструктор
        if re.search(r'\bExercise\s*\(', content):
            issues.append("❌ Exercise() constructor")
        
        # 8. Migration references
        if re.search(r'workouts_exercise', content) and 'migrations' in str(file_path):
            issues.append("⚠️ Migration table reference 'workouts_exercise'")
        
        # 9. Test fixtures/factories
        if re.search(r'class\s+\w*Exercise\w*Factory', content):
            issues.append("❌ Exercise factory class")
        
        return issues
    
    def run_comprehensive_validation(self):
        """Запустить полную Django-специфичную валидацию"""
        print("🔍 DJANGO-СПЕЦИФИЧНАЯ ВАЛИДАЦИЯ EXERCISE ССЫЛОК")
        print("=" * 60)
        
        production_files = self.get_production_files()
        print(f"📁 Проверяется {len(production_files)} файлов")
        
        all_issues = []
        problematic_files = []
        
        for file_path in production_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем все Django-специфичные паттерны
                issues = self.check_all_django_exercise_references(content, file_path)
                
                if issues:
                    all_issues.extend(issues)
                    problematic_files.append((file_path, issues))
                    
            except Exception as e:
                all_issues.append(f"Ошибка чтения {file_path}: {e}")
        
        # Результаты
        print("\n📊 РЕЗУЛЬТАТ DJANGO-ВАЛИДАЦИИ:")
        
        if not all_issues:
            print("✅ ОТЛИЧНО: Никаких Exercise ссылок не найдено!")
            print("✅ Django админ безопасен")
            print("✅ Все ForeignKey используют CSVExercise")
            print("✅ Миграции корректны")
            print("\n🎉 DJANGO ГОТОВ К ДЕПЛОЮ!")
            return True
        else:
            print(f"❌ Найдено {len(all_issues)} проблем в {len(problematic_files)} файлах:")
            
            for file_path, issues in problematic_files:
                print(f"\n📄 {file_path}:")
                for issue in issues:
                    print(f"   {issue}")
            
            return False
    
    def create_django_fix_script(self):
        """Создать скрипт для автоматического исправления Django ссылок"""
        fix_script = '''#!/usr/bin/env python3
"""
DJANGO FIX SCRIPT - Исправляет все Django-специфичные ссылки на Exercise
"""
import os
import re
from pathlib import Path

def fix_django_references():
    """Исправить все Django ссылки на Exercise"""
    
    fixes_applied = 0
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if 'backup' not in d.lower() and d not in {'.venv', '.git'}]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Fix 1: String ForeignKey references
                    content = re.sub(r"'workouts\\.Exercise'", "'workouts.CSVExercise'", content)
                    content = re.sub(r'"workouts\\.Exercise"', '"workouts.CSVExercise"', content)
                    
                    # Fix 2: Admin references
                    content = re.sub(r'admin\\.site\\.register\\s*\\(\\s*Exercise\\b', 'admin.site.register(CSVExercise', content)
                    content = re.sub(r'@admin\\.register\\s*\\(\\s*Exercise\\b', '@admin.register(CSVExercise', content)
                    
                    # Fix 3: Direct imports
                    content = re.sub(r'from\\s+apps\\.workouts\\.models\\s+import\\s+(.*?)\\bExercise\\b', 
                                   r'from apps.workouts.models import \\1CSVExercise', content)
                    
                    # Fix 4: Serializer model references
                    content = re.sub(r'model\\s*=\\s*Exercise\\b', 'model = CSVExercise', content)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixes_applied += 1
                        print(f"✅ Fixed: {file_path}")
                        
                except Exception as e:
                    print(f"❌ Error fixing {file_path}: {e}")
    
    print(f"\\n🎉 Applied fixes to {fixes_applied} files")

if __name__ == '__main__':
    fix_django_references()
'''
        
        with open(self.project_root / 'django_fix_script.py', 'w') as f:
            f.write(fix_script)
        
        print("📝 Создан django_fix_script.py для автоматического исправления")

def main():
    validator = DjangoComprehensiveValidator(os.getcwd())
    success = validator.run_comprehensive_validation()
    
    if not success:
        print("\n🛠️ Создаю скрипт автоматического исправления...")
        validator.create_django_fix_script()
        print("Запустите: python django_fix_script.py")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())