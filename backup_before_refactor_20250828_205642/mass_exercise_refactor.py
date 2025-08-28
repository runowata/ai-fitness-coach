#!/usr/bin/env python3
"""
РЕВОЛЮЦИОННЫЙ АВТОМАТИЗИРОВАННЫЙ РЕФАКТОРИНГ
Массовая замена всех остатков Exercise модели на CSVExercise
"""
import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import shutil
from datetime import datetime


class MassExerciseRefactor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / f"backup_before_refactor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.files_modified = []
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'exercise_imports_fixed': 0,
            'exercise_objects_fixed': 0,
            'muscle_groups_fixed': 0,
            'field_references_fixed': 0
        }
        
        # Паттерны для замены
        self.replacement_patterns = [
            # 1. Импорты Exercise
            {
                'pattern': r'from apps\.workouts\.models import ([^,\n]*,\s*)?Exercise([,\s][^,\n]*)?',
                'replacement': lambda m: f"from apps.workouts.models import {m.group(1) if m.group(1) else ''}CSVExercise{m.group(2) if m.group(2) else ''}",
                'description': 'Exercise import replacement'
            },
            {
                'pattern': r'from \.models import ([^,\n]*,\s*)?Exercise([,\s][^,\n]*)?',
                'replacement': lambda m: f"from .models import {m.group(1) if m.group(1) else ''}CSVExercise{m.group(2) if m.group(2) else ''}",
                'description': 'Relative Exercise import replacement'
            },
            
            # 2. Exercise.objects -> CSVExercise.objects
            {
                'pattern': r'\bExercise\.objects\b',
                'replacement': 'CSVExercise.objects',
                'description': 'Exercise.objects replacement'
            },
            
            # 3. Exercise.DoesNotExist -> CSVExercise.DoesNotExist
            {
                'pattern': r'\bExercise\.DoesNotExist\b',
                'replacement': 'CSVExercise.DoesNotExist',
                'description': 'Exercise.DoesNotExist replacement'
            },
            
            # 4. Exercise( -> CSVExercise(
            {
                'pattern': r'\bExercise\(',
                'replacement': 'CSVExercise(',
                'description': 'Exercise constructor replacement'
            },
            
            # 5. spec=Exercise -> spec=CSVExercise (для Mock)
            {
                'pattern': r'spec=Exercise\b',
                'replacement': 'spec=CSVExercise',
                'description': 'Mock spec replacement'
            },
            
            # 6. @admin.register(Exercise) -> удалить (уже удалено из models)
            {
                'pattern': r'@admin\.register\(Exercise\)',
                'replacement': '# @admin.register(Exercise) - REMOVED in Phase 5.6',
                'description': 'Admin register removal'
            }
        ]
        
        # Сложные паттерны, требующие контекстного анализа
        self.complex_patterns = [
            # Замена полей Exercise модели на CSVExercise поля
            'exercise.slug -> exercise.id',
            'exercise.name -> exercise.name_ru', 
            'exercise.difficulty -> exercise.level',
            'muscle_groups -> удалить или заменить на ai_tags'
        ]
    
    def create_backup(self):
        """Создать резервную копию проекта"""
        print(f"📦 Создание резервной копии в {self.backup_dir}")
        
        # Создаём директорию бэкапа
        self.backup_dir.mkdir(exist_ok=True)
        
        # Копируем все Python файлы
        for root, dirs, files in os.walk(self.project_root):
            # Пропускаем .venv, .git и backup директории
            dirs[:] = [d for d in dirs if d not in {'.venv', 'venv', '.git', '__pycache__', 'backup_before_refactor'}]
            
            for file in files:
                if file.endswith('.py'):
                    src_path = Path(root) / file
                    rel_path = src_path.relative_to(self.project_root)
                    dst_path = self.backup_dir / rel_path
                    
                    # Создаём директорию если не существует
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)
        
        print(f"✅ Резервная копия создана: {len(list(self.backup_dir.rglob('*.py')))} файлов")
    
    def get_python_files(self) -> List[Path]:
        """Получить список всех Python файлов для обработки"""
        python_files = []
        exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', 'node_modules', 'env'}
        
        # Добавляем backup директории в исключения
        exclude_dirs.update({d.name for d in self.project_root.glob('backup_before_refactor_*')})
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        return python_files
    
    def refactor_file(self, file_path: Path) -> bool:
        """Рефакторинг одного файла"""
        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            modified_content = original_content
            file_modified = False
            changes_made = []
            
            # Применяем все паттерны замены
            for pattern_info in self.replacement_patterns:
                pattern = pattern_info['pattern']
                replacement = pattern_info['replacement']
                description = pattern_info['description']
                
                if callable(replacement):
                    # Сложная замена с функцией
                    def repl_func(match):
                        return replacement(match)
                    new_content, count = re.subn(pattern, repl_func, modified_content)
                else:
                    # Простая замена
                    new_content, count = re.subn(pattern, replacement, modified_content)
                
                if count > 0:
                    modified_content = new_content
                    file_modified = True
                    changes_made.append(f"{description}: {count} замен")
                    
                    # Обновляем статистику
                    if 'import' in description:
                        self.stats['exercise_imports_fixed'] += count
                    elif 'objects' in description:
                        self.stats['exercise_objects_fixed'] += count
                    elif 'muscle_groups' in description:
                        self.stats['muscle_groups_fixed'] += count
                    else:
                        self.stats['field_references_fixed'] += count
            
            # Специальные исправления для CSVExercise полей
            field_fixes = self.fix_csvexercise_fields(modified_content)
            if field_fixes['content'] != modified_content:
                modified_content = field_fixes['content']
                file_modified = True
                changes_made.extend(field_fixes['changes'])
            
            # Если файл изменился, сохраняем его
            if file_modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                self.files_modified.append(str(file_path))
                self.stats['files_modified'] += 1
                
                print(f"✅ Изменён: {file_path}")
                for change in changes_made:
                    print(f"   - {change}")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка обработки {file_path}: {e}")
            return False
    
    def fix_csvexercise_fields(self, content: str) -> Dict[str, any]:
        """Исправление полей для работы с CSVExercise"""
        modified_content = content
        changes = []
        
        # 1. exercise.slug -> exercise.id (CSVExercise использует id вместо slug)
        pattern = r'(\w+)\.slug'
        def slug_replacement(match):
            var_name = match.group(1)
            # Проверяем контекст - если это exercise/ex переменная
            if var_name in ['exercise', 'ex', 'e']:
                return f'{var_name}.id'
            return match.group(0)  # Не изменяем другие .slug
        
        new_content, count = re.subn(pattern, slug_replacement, modified_content)
        if count > 0:
            modified_content = new_content
            changes.append(f"exercise.slug -> exercise.id: {count} замен")
        
        # 2. exercise.name -> exercise.name_ru (предпочтительно русское имя)
        pattern = r'(\w+)\.name(?!\w)'  # name но не name_ru или name_en
        def name_replacement(match):
            var_name = match.group(1)
            if var_name in ['exercise', 'ex', 'e']:
                return f'{var_name}.name_ru'
            return match.group(0)
        
        new_content, count = re.subn(pattern, name_replacement, modified_content)
        if count > 0:
            modified_content = new_content
            changes.append(f"exercise.name -> exercise.name_ru: {count} замен")
        
        # 3. exercise.difficulty -> exercise.level
        pattern = r'(\w+)\.difficulty\b'
        def difficulty_replacement(match):
            var_name = match.group(1)
            if var_name in ['exercise', 'ex', 'e']:
                return f'{var_name}.level'
            return match.group(0)
        
        new_content, count = re.subn(pattern, difficulty_replacement, modified_content)
        if count > 0:
            modified_content = new_content
            changes.append(f"exercise.difficulty -> exercise.level: {count} замен")
        
        # 4. Исправление создания Exercise объектов
        # Exercise.objects.create(slug=..., name=..., difficulty=...) ->
        # CSVExercise.objects.create(id=..., name_ru=..., level=...)
        
        # Ищем паттерны создания Exercise
        create_pattern = r'CSVExercise\.objects\.create\((.*?)\)'
        
        def fix_create_params(match):
            params = match.group(1)
            # Заменяем параметры
            params = re.sub(r'slug=', 'id=', params)
            params = re.sub(r'name=([^,\)]+)', r'name_ru=\1, name_en=\1', params)
            params = re.sub(r'difficulty=', 'level=', params)
            
            # Добавляем обязательные поля если их нет
            if 'muscle_group=' not in params:
                params += ', muscle_group="full_body"'
            if 'exercise_type=' not in params:
                params += ', exercise_type="strength"'
            if 'is_active=' not in params:
                params += ', is_active=True'
            
            return f'CSVExercise.objects.create({params})'
        
        new_content = re.sub(create_pattern, fix_create_params, modified_content)
        if new_content != modified_content:
            modified_content = new_content
            changes.append("Исправлены параметры CSVExercise.objects.create()")
        
        return {
            'content': modified_content,
            'changes': changes
        }
    
    def run_mass_refactor(self):
        """Запуск массового рефакторинга"""
        print("🚀 НАЧАЛО МАССОВОГО РЕФАКТОРИНГА")
        print("=" * 60)
        
        # 1. Создаём backup
        self.create_backup()
        
        # 2. Получаем список файлов
        python_files = self.get_python_files()
        print(f"📁 Найдено {len(python_files)} Python файлов для обработки")
        
        # 3. Обрабатываем каждый файл
        print("\n🔧 ОБРАБОТКА ФАЙЛОВ:")
        for i, file_path in enumerate(python_files, 1):
            self.stats['files_processed'] += 1
            
            # Показываем прогресс
            if i % 10 == 0:
                print(f"   Прогресс: {i}/{len(python_files)} файлов")
            
            self.refactor_file(file_path)
        
        # 4. Выводим статистику
        self.print_statistics()
        
        # 5. Проверяем результат
        self.validate_refactoring()
    
    def print_statistics(self):
        """Вывод статистики изменений"""
        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА РЕФАКТОРИНГА:")
        print(f"   Файлов обработано: {self.stats['files_processed']}")
        print(f"   Файлов изменено: {self.stats['files_modified']}")
        print(f"   Exercise импортов исправлено: {self.stats['exercise_imports_fixed']}")
        print(f"   Exercise.objects исправлено: {self.stats['exercise_objects_fixed']}")
        print(f"   muscle_groups исправлено: {self.stats['muscle_groups_fixed']}")
        print(f"   Других полей исправлено: {self.stats['field_references_fixed']}")
        
        total_fixes = (self.stats['exercise_imports_fixed'] + 
                      self.stats['exercise_objects_fixed'] + 
                      self.stats['muscle_groups_fixed'] + 
                      self.stats['field_references_fixed'])
        print(f"   ВСЕГО ИСПРАВЛЕНИЙ: {total_fixes}")
        
        if self.files_modified:
            print(f"\n📝 ИЗМЕНЁННЫЕ ФАЙЛЫ ({len(self.files_modified)}):")
            for file_path in self.files_modified[:10]:  # Показываем первые 10
                print(f"   - {file_path}")
            if len(self.files_modified) > 10:
                print(f"   ... и ещё {len(self.files_modified) - 10} файлов")
    
    def validate_refactoring(self):
        """Быстрая валидация результатов рефакторинга"""
        print("\n🔍 БЫСТРАЯ ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ:")
        
        # Проверяем оставшиеся Exercise ссылки
        remaining_exercise_refs = 0
        remaining_files = []
        
        python_files = self.get_python_files()
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ищем проблемные паттерны
                problematic_patterns = [
                    r'\bExercise\.objects\b',
                    r'\bExercise\.DoesNotExist\b',
                    r'from.*Exercise(?!Validation)',  # Exercise но не ExerciseValidation
                    r'import.*Exercise(?!Validation)'
                ]
                
                file_has_issues = False
                for pattern in problematic_patterns:
                    if re.search(pattern, content):
                        if not file_has_issues:
                            remaining_files.append(str(file_path))
                            file_has_issues = True
                        remaining_exercise_refs += len(re.findall(pattern, content))
                        
            except Exception as e:
                print(f"❌ Ошибка проверки {file_path}: {e}")
        
        if remaining_exercise_refs == 0:
            print("✅ РЕФАКТОРИНГ УСПЕШЕН! Остатков Exercise не найдено.")
        else:
            print(f"⚠️  Найдено {remaining_exercise_refs} оставшихся ссылок на Exercise в {len(remaining_files)} файлах:")
            for file_path in remaining_files[:5]:
                print(f"   - {file_path}")
            if len(remaining_files) > 5:
                print(f"   ... и ещё {len(remaining_files) - 5} файлов")
    
    def rollback_changes(self):
        """Откат изменений из backup"""
        if not self.backup_dir.exists():
            print("❌ Backup не найден, откат невозможен")
            return False
        
        print(f"🔄 Откат изменений из {self.backup_dir}")
        
        # Восстанавливаем все файлы из backup
        for backup_file in self.backup_dir.rglob('*.py'):
            rel_path = backup_file.relative_to(self.backup_dir)
            original_file = self.project_root / rel_path
            
            if original_file.exists():
                shutil.copy2(backup_file, original_file)
        
        print("✅ Откат завершён")
        return True


def main():
    """Главная функция"""
    print("🚀 МАССОВЫЙ АВТОМАТИЗИРОВАННЫЙ РЕФАКТОРИНГ")
    print("Замена всех Exercise → CSVExercise")
    print("=" * 60)
    
    project_root = os.getcwd()
    refactor = MassExerciseRefactor(project_root)
    
    # Подтверждение от пользователя
    print("⚠️  ВНИМАНИЕ: Будут изменены ВСЕ Python файлы в проекте!")
    print(f"Проект: {project_root}")
    print("Будет создана резервная копия перед изменениями.")
    
    confirm = input("\nПродолжить? (yes/y для подтверждения): ").lower()
    if confirm not in ['yes', 'y']:
        print("❌ Отменено пользователем")
        return
    
    try:
        # Запускаем рефакторинг
        refactor.run_mass_refactor()
        
        print("\n🎉 МАССОВЫЙ РЕФАКТОРИНГ ЗАВЕРШЁН!")
        print("Проверьте результаты и запустите тесты.")
        
        # Предлагаем откат если что-то пошло не так
        rollback = input("\nЕсли нужен откат, введите 'rollback': ").lower()
        if rollback == 'rollback':
            refactor.rollback_changes()
        
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        rollback = input("Нужен откат изменений? (y/n): ").lower()
        if rollback == 'y':
            refactor.rollback_changes()
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Рекомендуется откат изменений")
        rollback = input("Выполнить откат? (y/n): ").lower()
        if rollback == 'y':
            refactor.rollback_changes()


if __name__ == '__main__':
    main()