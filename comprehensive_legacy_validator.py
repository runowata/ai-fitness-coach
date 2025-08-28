#!/usr/bin/env python3
"""
РЕВОЛЮЦИОННЫЙ ВАЛИДАТОР LEGACY КОДА
Полностью автоматизированная система обнаружения всех остатков Exercise модели
"""
import ast
import os
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
import subprocess


class ComprehensiveLegacyValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_files = []
        self.errors = []
        self.warnings = []
        self.legacy_patterns = {
            # Строго запрещённые паттерны
            'forbidden_imports': [
                'from apps.workouts.models import CSVExercise',
                'from .models import CSVExercise', 
                'import Exercise',
            ],
            'forbidden_references': [
                'CSVExercise.objects',
                'CSVExercise.DoesNotExist',
                'CSVExercise(',
                'Exercise.Meta',
                '# @admin.register(Exercise) - REMOVED in Phase 5.6',
            ],
            'forbidden_fields': [
                'muscle_groups',
                'equipment_needed', 
                # 'alternatives' - удалено, чтобы избежать false positives в validator
            ],
            # Подозрительные паттерны (требуют проверки)
            'suspicious_patterns': [
                'muscle_group[^_s]',  # muscle_group но не muscle_groups или muscle_group_count
                'equipment.*need',
                'alternative.*relationship',
                'Exercise[^V]',  # Exercise но не ExerciseValidation
            ]
        }
        
    def scan_all_python_files(self):
        """Найти все Python файлы в проекте"""
        print("🔍 Сканирование всех Python файлов...")
        
        exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', 'node_modules', 'env'}
        
        for root, dirs, files in os.walk(self.project_root):
            # Исключаем ненужные директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    self.python_files.append(file_path)
                    
        print(f"✅ Найдено {len(self.python_files)} Python файлов")
        return self.python_files
    
    def validate_syntax(self) -> List[Tuple[str, str]]:
        """Проверить синтаксис всех Python файлов"""
        print("\n🔍 СИНТАКСИЧЕСКАЯ ВАЛИДАЦИЯ...")
        syntax_errors = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    
                ast.parse(code, filename=str(file_path))
                
            except SyntaxError as e:
                error_msg = f"Синтаксическая ошибка: строка {e.lineno}: {e.msg}"
                syntax_errors.append((str(file_path), error_msg))
                print(f"❌ {file_path}: {error_msg}")
                
            except UnicodeDecodeError as e:
                error_msg = f"Ошибка кодировки: {e}"
                syntax_errors.append((str(file_path), error_msg))
                print(f"❌ {file_path}: {error_msg}")
                
        if not syntax_errors:
            print("✅ Все файлы синтаксически корректны")
            
        return syntax_errors
    
    def analyze_ast_imports(self) -> Dict[str, List[str]]:
        """Анализ AST для поиска всех импортов"""
        print("\n🔍 AST АНАЛИЗ ИМПОРТОВ...")
        import_analysis = {}
        forbidden_found = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                tree = ast.parse(code, filename=str(file_path))
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(f"import {alias.name}")
                            
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"from {module} import {alias.name}")
                
                import_analysis[str(file_path)] = imports
                
                # Проверяем на запрещённые импорты
                for imp in imports:
                    for forbidden in self.legacy_patterns['forbidden_imports']:
                        if forbidden in imp:
                            forbidden_found.append((str(file_path), imp))
                            print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: {file_path}")
                            print(f"   Запрещённый импорт: {imp}")
                            
            except Exception as e:
                print(f"❌ Ошибка анализа AST {file_path}: {e}")
                
        if not forbidden_found:
            print("✅ Запрещённые импорты не найдены")
            
        return import_analysis
    
    def search_forbidden_patterns(self) -> Dict[str, List[Tuple[int, str]]]:
        """Поиск запрещённых паттернов в коде"""
        print("\n🔍 ПОИСК ЗАПРЕЩЁННЫХ ПАТТЕРНОВ...")
        violations = {}
        
        for file_path in self.python_files:
            file_violations = []
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_clean = line.strip()
                    
                    # Проверяем запрещённые ссылки
                    for forbidden in self.legacy_patterns['forbidden_references']:
                        if forbidden in line_clean and not line_clean.startswith('#'):
                            file_violations.append((line_num, f"Запрещённая ссылка: {forbidden}"))
                            print(f"🚨 {file_path}:{line_num} - {forbidden}")
                    
                    # Проверяем запрещённые поля (только если это не комментарий)
                    if not line_clean.startswith('#'):
                        for field in self.legacy_patterns['forbidden_fields']:
                            if field in line_clean:
                                # Дополнительная проверка контекста
                                if self._is_legacy_field_usage(line_clean, field):
                                    file_violations.append((line_num, f"Запрещённое поле: {field}"))
                                    print(f"🚨 {file_path}:{line_num} - поле {field}")
            
            except Exception as e:
                print(f"❌ Ошибка чтения {file_path}: {e}")
                
            if file_violations:
                violations[str(file_path)] = file_violations
                
        if not violations:
            print("✅ Запрещённые паттерны не найдены")
            
        return violations
    
    def _is_legacy_field_usage(self, line: str, field: str) -> bool:
        """Определить, является ли использование поля legacy"""
        # Игнорируем комментарии и допустимые контексты
        if line.startswith('#'):
            return False
            
        if field == 'muscle_groups':
            # Допустимо: muscle_group_count, muscle_group_distribution
            if 'muscle_group_count' in line or 'muscle_group_distribution' in line:
                return False
            # Недопустимо: прямое использование muscle_groups
            return 'muscle_groups' in line
            
        elif field == 'equipment_needed':
            # Недопустимо любое использование
            return True
            
        # elif field == 'alternatives':
        #     # Допустимо: функции alternatives, get_alternatives
        #     # Недопустимо: поле модели .alternatives  
        #     return '.alternatives' in line or 'alternatives=' in line
            
        return True
    
    def test_django_imports(self) -> List[str]:
        """Тестирование Django импортов"""
        print("\n🔍 ТЕСТИРОВАНИЕ DJANGO ИМПОРТОВ...")
        
        # Устанавливаем Django окружение
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
        
        try:
            import django
            django.setup()
            print("✅ Django setup успешен")
        except Exception as e:
            print(f"❌ Ошибка Django setup: {e}")
            return [f"Django setup failed: {e}"]
        
        import_errors = []
        
        # Тестируем критические импорты
        critical_imports = [
            'apps.workouts.models.CSVExercise',
            'apps.workouts.models.VideoClip', 
            'apps.workouts.models.WorkoutPlan',
            'apps.ai_integration.fallback_service.FallbackService',
            'apps.core.services.exercise_validation.ExerciseValidationService'
        ]
        
        for module_path in critical_imports:
            try:
                module_parts = module_path.split('.')
                module_name = '.'.join(module_parts[:-1])
                class_name = module_parts[-1]
                
                module = importlib.import_module(module_name)
                getattr(module, class_name)
                
                print(f"✅ {module_path}")
                
            except ImportError as e:
                error_msg = f"Import failed: {module_path} - {e}"
                import_errors.append(error_msg)
                print(f"❌ {error_msg}")
                
            except AttributeError as e:
                error_msg = f"Class not found: {module_path} - {e}"
                import_errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        # Тестируем запрещённые импорты
        forbidden_tests = [
            'apps.workouts.models.Exercise',
            'apps.workouts.admin.ExerciseAdmin'
        ]
        
        for forbidden_import in forbidden_tests:
            try:
                module_parts = forbidden_import.split('.')
                module_name = '.'.join(module_parts[:-1])
                class_name = module_parts[-1]
                
                module = importlib.import_module(module_name)
                getattr(module, class_name)
                
                error_msg = f"КРИТИЧЕСКАЯ ОШИБКА: Запрещённый класс всё ещё существует: {forbidden_import}"
                import_errors.append(error_msg)
                print(f"🚨 {error_msg}")
                
            except (ImportError, AttributeError):
                print(f"✅ Запрещённый класс правильно удалён: {forbidden_import}")
        
        return import_errors
    
    def run_static_analysis(self) -> Dict[str, str]:
        """Запуск статических анализаторов"""
        print("\n🔍 СТАТИЧЕСКИЙ АНАЛИЗ КОДА...")
        
        results = {}
        
        # Запускаем flake8
        try:
            result = subprocess.run(
                ['flake8', '--select=F,E999', '--exclude=.venv,venv,migrations', '.'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            results['flake8'] = result.stdout if result.stdout else "Без ошибок"
            print(f"✅ flake8 завершён")
        except Exception as e:
            results['flake8'] = f"Ошибка запуска: {e}"
            print(f"❌ flake8 ошибка: {e}")
        
        return results
    
    def generate_comprehensive_report(self) -> str:
        """Генерация полного отчёта"""
        print("\n📊 ГЕНЕРАЦИЯ ПОЛНОГО ОТЧЁТА...")
        
        # Запускаем все проверки
        syntax_errors = self.validate_syntax()
        import_analysis = self.analyze_ast_imports()
        pattern_violations = self.search_forbidden_patterns()
        django_errors = self.test_django_imports()
        static_analysis = self.run_static_analysis()
        
        # Формируем отчёт
        report = "# COMPREHENSIVE LEGACY VALIDATION REPORT\n\n"
        
        report += f"## ОБЩАЯ СТАТИСТИКА\n"
        report += f"- Всего Python файлов: {len(self.python_files)}\n"
        report += f"- Синтаксических ошибок: {len(syntax_errors)}\n"
        report += f"- Нарушений паттернов: {sum(len(v) for v in pattern_violations.values())}\n"
        report += f"- Django ошибок: {len(django_errors)}\n\n"
        
        if syntax_errors:
            report += "## 🚨 СИНТАКСИЧЕСКИЕ ОШИБКИ\n"
            for file_path, error in syntax_errors:
                report += f"- {file_path}: {error}\n"
            report += "\n"
        
        if pattern_violations:
            report += "## 🚨 НАРУШЕНИЯ LEGACY ПАТТЕРНОВ\n"
            for file_path, violations in pattern_violations.items():
                report += f"### {file_path}\n"
                for line_num, violation in violations:
                    report += f"- Строка {line_num}: {violation}\n"
                report += "\n"
        
        if django_errors:
            report += "## 🚨 DJANGO ИМПОРТ ОШИБКИ\n"
            for error in django_errors:
                report += f"- {error}\n"
            report += "\n"
        
        # Статус валидации
        total_errors = len(syntax_errors) + len(django_errors) + sum(len(v) for v in pattern_violations.values())
        
        if total_errors == 0:
            report += "## ✅ ВАЛИДАЦИЯ ПРОЙДЕНА\n"
            report += "Все проверки успешны. Legacy код полностью очищен.\n"
        else:
            report += f"## ❌ ВАЛИДАЦИЯ НЕ ПРОЙДЕНА\n"
            report += f"Найдено {total_errors} критических проблем, требующих исправления.\n"
        
        return report


def main():
    print("🚀 ЗАПУСК РЕВОЛЮЦИОННОЙ ДИАГНОСТИКИ LEGACY КОДА")
    print("=" * 60)
    
    project_root = os.getcwd()
    validator = ComprehensiveLegacyValidator(project_root)
    
    # Сканируем файлы
    validator.scan_all_python_files()
    
    # Генерируем полный отчёт
    report = validator.generate_comprehensive_report()
    
    # Сохраняем отчёт
    report_path = Path(project_root) / "LEGACY_VALIDATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Полный отчёт сохранён: {report_path}")
    
    # Выводим краткое резюме
    print("\n" + "=" * 60)
    print("📊 КРАТКОЕ РЕЗЮМЕ:")
    lines = report.split('\n')
    for line in lines:
        if '🚨' in line or '✅' in line or '❌' in line:
            print(line)
    
    return report


if __name__ == '__main__':
    main()