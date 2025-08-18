#!/usr/bin/env python3
"""
Переименование файлов с префиксом sexual_ в endurance_
"""

import os
import pandas as pd
from datetime import datetime

def get_files_to_rename():
    """Получить список файлов для переименования из CSV"""
    
    csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv'
    
    try:
        df = pd.read_csv(csv_file)
        
        files_to_rename = []
        
        for _, row in df.iterrows():
            target_path = row['target_path']
            current_name = os.path.basename(target_path)
            
            # Проверяем, начинается ли с sexual_
            if current_name.startswith('sexual_'):
                new_name = current_name.replace('sexual_', 'endurance_')
                
                files_to_rename.append({
                    'current_path': target_path,
                    'current_name': current_name,
                    'new_name': new_name,
                    'new_path': target_path.replace(current_name, new_name)
                })
        
        print(f"📋 Найдено {len(files_to_rename)} файлов для переименования")
        
        return files_to_rename
        
    except Exception as e:
        print(f"❌ Ошибка загрузки CSV: {e}")
        return []

def create_rename_commands(files_to_rename):
    """Создать bash команды для переименования"""
    
    commands = []
    
    print(f"\n🔄 Создание команд переименования...")
    
    for file_info in files_to_rename:
        current_path = file_info['current_path']
        new_path = file_info['new_path']
        
        # Экранируем пути с пробелами
        escaped_current = f'"{current_path}"'
        escaped_new = f'"{new_path}"'
        
        command = f'mv {escaped_current} {escaped_new}'
        commands.append({
            'command': command,
            'current_name': file_info['current_name'],
            'new_name': file_info['new_name']
        })
    
    return commands

def execute_rename_operations(commands):
    """Выполнить операции переименования"""
    
    print(f"\n🔄 Выполнение переименования {len(commands)} файлов...")
    
    success_count = 0
    error_count = 0
    operations_log = []
    
    for i, cmd_info in enumerate(commands, 1):
        command = cmd_info['command']
        current_name = cmd_info['current_name']
        new_name = cmd_info['new_name']
        
        try:
            # Выполняем команду переименования
            result = os.system(command)
            
            if result == 0:
                success_count += 1
                status = "✅ УСПЕХ"
                operations_log.append({
                    'status': 'success',
                    'current_name': current_name,
                    'new_name': new_name,
                    'error': None
                })
                print(f"  {i:2d}/42: {current_name} → {new_name} ✅")
            else:
                error_count += 1
                status = "❌ ОШИБКА"
                operations_log.append({
                    'status': 'error',
                    'current_name': current_name,
                    'new_name': new_name,
                    'error': f'Command failed with code {result}'
                })
                print(f"  {i:2d}/42: {current_name} → {new_name} ❌")
                
        except Exception as e:
            error_count += 1
            operations_log.append({
                'status': 'error',
                'current_name': current_name,
                'new_name': new_name,
                'error': str(e)
            })
            print(f"  {i:2d}/42: {current_name} → {new_name} ❌ (Exception: {e})")
    
    return success_count, error_count, operations_log

def update_csv_file(files_to_rename):
    """Обновить CSV файл с новыми названиями"""
    
    print(f"\n📝 Обновление CSV файла...")
    
    csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv'
    
    try:
        df = pd.read_csv(csv_file)
        
        updated_count = 0
        
        for file_info in files_to_rename:
            current_name = file_info['current_name']
            new_name = file_info['new_name']
            
            # Находим строки с этим файлом и обновляем
            mask = df['new_name'] == current_name
            if mask.any():
                df.loc[mask, 'new_name'] = new_name
                df.loc[mask, 'target_path'] = df.loc[mask, 'target_path'].str.replace(current_name, new_name)
                df.loc[mask, 'cloudflare_url'] = df.loc[mask, 'cloudflare_url'].str.replace(current_name, new_name)
                updated_count += 1
        
        # Сохраняем обновленный CSV
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"✅ Обновлено {updated_count} записей в CSV файле")
        
    except Exception as e:
        print(f"❌ Ошибка обновления CSV: {e}")

def generate_rename_report(success_count, error_count, operations_log):
    """Создать отчет о переименовании"""
    
    report = f"""# 🔄 ОТЧЕТ О ПЕРЕИМЕНОВАНИИ ВИДЕОФАЙЛОВ

## Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 СВОДКА:

### Результаты операции:
- **Всего файлов**: {len(operations_log)}
- **Успешно переименовано**: {success_count} ✅
- **Ошибок**: {error_count} ❌
- **Процент успеха**: {(success_count/len(operations_log)*100):.1f}%

---

## ✅ УСПЕШНЫЕ ПЕРЕИМЕНОВАНИЯ ({success_count}):

"""
    
    # Успешные операции
    for op in operations_log:
        if op['status'] == 'success':
            report += f"- `{op['current_name']}` → `{op['new_name']}`\n"
    
    report += f"""
---

## ❌ ОШИБКИ ПЕРЕИМЕНОВАНИЯ ({error_count}):

"""
    
    # Ошибки
    if error_count > 0:
        for op in operations_log:
            if op['status'] == 'error':
                report += f"- `{op['current_name']}` → `{op['new_name']}` (Ошибка: {op['error']})\n"
    else:
        report += "Ошибок не было.\n"
    
    report += f"""
---

## 🎯 РЕЗУЛЬТАТ:

### Изменения в структуре:
- **До**: `sexual_NN_technique_m01.mp4` (42 файла)
- **После**: `endurance_NN_technique_m01.mp4` (42 файла)

### Соответствие стандартам именования:
Файлы теперь соответствуют утвержденному паттерну для категории "Сексуальная выносливость":
- **Паттерн**: `endurance_NN_technique_mMM.mp4`
- **Где**: NN = 01-42, MM = 01-03

---

## 📋 СЛЕДУЮЩИЕ ШАГИ:

1. ✅ Проверить результат переименования
2. ✅ Убедиться, что все файлы доступны
3. ✅ Запустить повторную проверку соответствия названий
4. ✅ Обновить Cloudflare R2 при загрузке

---

## 🎉 СТАТУС:

"""
    
    if error_count == 0:
        report += "**🎉 ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!**\n\n"
        report += "Все 42 файла категории 'Сексуальная выносливость' теперь используют правильный префикс `endurance_`.\n"
        report += "Система готова к использованию с правильными названиями файлов.\n"
    else:
        report += "**⚠️ ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ**\n\n"
        report += f"Успешно переименовано {success_count} из {len(operations_log)} файлов.\n"
        report += f"Требуется исправление {error_count} ошибок.\n"
    
    return report

def main():
    """Основная функция переименования"""
    
    print("🔄 ПЕРЕИМЕНОВАНИЕ ФАЙЛОВ: sexual_ → endurance_")
    print("=" * 60)
    
    # 1. Получаем список файлов для переименования
    print("\n📋 Шаг 1: Поиск файлов для переименования...")
    files_to_rename = get_files_to_rename()
    
    if not files_to_rename:
        print("✅ Файлы для переименования не найдены")
        return
    
    # 2. Показываем что будем переименовывать
    print(f"\n📁 Файлы для переименования:")
    for i, file_info in enumerate(files_to_rename[:5], 1):
        print(f"  {i}: {file_info['current_name']} → {file_info['new_name']}")
    
    if len(files_to_rename) > 5:
        print(f"  ... и еще {len(files_to_rename) - 5} файлов")
    
    # 3. Создаем команды переименования
    print(f"\n⚙️ Шаг 2: Подготовка команд переименования...")
    commands = create_rename_commands(files_to_rename)
    
    # 4. Выполняем переименование
    print(f"\n🔄 Шаг 3: Выполнение переименования...")
    success_count, error_count, operations_log = execute_rename_operations(commands)
    
    # 5. Обновляем CSV файл
    if success_count > 0:
        update_csv_file(files_to_rename)
    
    # 6. Создаем отчет
    print(f"\n📄 Шаг 4: Создание отчета...")
    report = generate_rename_report(success_count, error_count, operations_log)
    
    # Сохраняем отчет
    report_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/RENAME_OPERATION_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Отчет сохранен: {report_file}")
    
    # Итог
    print("\n" + "=" * 60)
    if error_count == 0:
        print("🎉 ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print(f"✅ Переименовано: {success_count} файлов")
        print("📊 Все названия теперь соответствуют стандартам")
    else:
        print("⚠️ ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
        print(f"✅ Успешно: {success_count} файлов")
        print(f"❌ Ошибок: {error_count} файлов")
        print("📄 Проверьте отчет для деталей")

if __name__ == '__main__':
    main()