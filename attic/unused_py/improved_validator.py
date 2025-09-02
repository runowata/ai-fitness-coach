#!/usr/bin/env python3
"""
IMPROVED SYSTEM VALIDATOR
Includes Python syntax validation to prevent deploy failures
"""

import os
import sys
import ast
import py_compile
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class ImprovedValidator:
    """Валидатор с проверкой синтаксиса Python"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def add_error(self, category: str, message: str, location: str = ""):
        self.errors.append({
            "level": "ERROR",
            "category": category,
            "message": message,
            "location": location
        })
        
    def check_python_syntax(self):
        """Проверка синтаксиса всех Python файлов"""
        print("🔍 Checking Python syntax...")
        
        python_files = list(Path.cwd().rglob('apps/**/*.py'))
        python_files.extend(list(Path.cwd().rglob('config/**/*.py')))
        
        for py_file in python_files:
            if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                # Проверка синтаксиса через compile
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                compile(content, str(py_file), 'exec')
                
            except SyntaxError as e:
                self.add_error(
                    "PYTHON_SYNTAX",
                    f"Syntax error: {e.msg}",
                    f"{py_file}:{e.lineno}"
                )
            except Exception as e:
                self.add_error(
                    "PYTHON_SYNTAX",
                    f"Failed to compile: {e}",
                    str(py_file)
                )
                
    def check_imports(self):
        """Проверка что все импорты корректны"""
        print("🔍 Checking imports...")
        
        # Список критически важных файлов
        critical_files = [
            'apps/onboarding/views.py',
            'apps/workouts/views.py',
            'apps/content/views.py',
            'config/urls.py',
        ]
        
        for file_path in critical_files:
            file = Path(file_path)
            if not file.exists():
                continue
                
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST для поиска импортов
                tree = ast.parse(content, str(file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Проверяем что модуль существует
                            module_parts = node.module.split('.')
                            if module_parts[0] == 'apps':
                                # Проверяем Django app
                                app_path = Path('/'.join(module_parts))
                                if not app_path.exists() and not (app_path.parent / '__init__.py').exists():
                                    self.add_error(
                                        "IMPORT_ERROR",
                                        f"Cannot import module: {node.module}",
                                        f"{file}:{node.lineno}"
                                    )
                                    
            except Exception as e:
                self.add_error(
                    "IMPORT_ERROR",
                    f"Failed to parse imports: {e}",
                    str(file)
                )
                
    def check_django_urls(self):
        """Проверка что URL patterns корректны"""
        print("🔍 Checking Django URLs...")
        
        try:
            # Простая проверка что urls.py компилируется
            result = subprocess.run([
                sys.executable, '-c',
                'import sys; sys.path.append("."); from config import urls'
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode != 0:
                self.add_error(
                    "DJANGO_URLS",
                    f"URL configuration error: {result.stderr}",
                    "config/urls.py"
                )
                
        except Exception as e:
            self.add_error(
                "DJANGO_URLS",
                f"Failed to check URLs: {e}",
                "config/urls.py"
            )
            
    def validate_all(self) -> Dict[str, Any]:
        """Запустить все проверки"""
        print("\n" + "="*60)
        print("🚀 IMPROVED SYSTEM VALIDATION")
        print("="*60 + "\n")
        
        # Критически важные проверки
        self.check_python_syntax()
        self.check_imports()
        self.check_django_urls()
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings)
            }
        }
        
    def print_report(self, results: Dict[str, Any]) -> bool:
        """Вывод отчета"""
        print("\n" + "="*60)
        print("📊 IMPROVED VALIDATION REPORT")
        print("="*60)
        
        if results['errors']:
            print(f"\n❌ CRITICAL ERRORS: {len(results['errors'])}")
            print("-"*40)
            for error in results['errors']:
                print(f"  [{error['category']}]")
                print(f"     {error['message']}")
                if error['location']:
                    print(f"     📍 {error['location']}")
                print()
                
        if results['summary']['total_errors'] == 0:
            print("✅ NO CRITICAL ERRORS FOUND!")
            print("🎉 System ready for deployment")
        else:
            print(f"❌ Found {results['summary']['total_errors']} CRITICAL ERRORS")
            print("\n🔧 FIX ALL ERRORS BEFORE DEPLOYMENT!")
            
        print("="*60 + "\n")
        return results['summary']['total_errors'] == 0


def main():
    validator = ImprovedValidator()
    results = validator.validate_all()
    success = validator.print_report(results)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())