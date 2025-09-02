#!/usr/bin/env python3
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
                    content = re.sub(r"'workouts\.Exercise'", "'workouts.CSVExercise'", content)
                    content = re.sub(r'"workouts\.Exercise"', '"workouts.CSVExercise"', content)
                    
                    # Fix 2: Admin references
                    content = re.sub(r'admin\.site\.register\s*\(\s*Exercise\b', 'admin.site.register(CSVExercise', content)
                    content = re.sub(r'@admin\.register\s*\(\s*Exercise\b', '@admin.register(CSVExercise', content)
                    
                    # Fix 3: Direct imports
                    content = re.sub(r'from\s+apps\.workouts\.models\s+import\s+(.*?)\bExercise\b', 
                                   r'from apps.workouts.models import \1CSVExercise', content)
                    
                    # Fix 4: Serializer model references
                    content = re.sub(r'model\s*=\s*Exercise\b', 'model = CSVExercise', content)
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixes_applied += 1
                        print(f"✅ Fixed: {file_path}")
                        
                except Exception as e:
                    print(f"❌ Error fixing {file_path}: {e}")
    
    print(f"\n🎉 Applied fixes to {fixes_applied} files")

if __name__ == '__main__':
    fix_django_references()
