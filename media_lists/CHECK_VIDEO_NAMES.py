#!/usr/bin/env python3
"""
Проверка соответствия названий видеофайлов с эталонными названиями из CSV
"""

import os
import pandas as pd
import csv
from pathlib import Path
import re

def load_reference_names():
    """Загрузить эталонные названия из CSV файла"""
    
    csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv'
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Загружено {len(df)} эталонных упражнений из CSV")
        
        # Извлекаем новые имена файлов
        reference_names = set()
        for _, row in df.iterrows():
            new_name = row['new_name']
            reference_names.add(new_name)
        
        print(f"📋 Найдено {len(reference_names)} уникальных эталонных названий")
        return reference_names, df
        
    except Exception as e:
        print(f"❌ Ошибка загрузки CSV: {e}")
        return None, None

def get_actual_video_names():
    """Получить фактические названия видео из папки exercises на Z9"""
    
    # Поскольку Z9 недоступен, проверим локально сохраненные списки
    actual_names = set()
    
    # Попробуем получить из CSV файла EXERCISES_271_VIDEOS.csv
    csv_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/EXERCISES_271_VIDEOS.csv'
    
    try:
        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            target_path = row['target_path']
            filename = os.path.basename(target_path)
            actual_names.add(filename)
        
        print(f"📁 Найдено {len(actual_names)} видеофайлов в папке exercises")
        return actual_names
        
    except Exception as e:
        print(f"❌ Ошибка получения фактических названий: {e}")
        return set()

def check_naming_patterns():
    """Проверить соответствие паттернам именования"""
    
    patterns = {
        'warmup': r'^warmup_\d{2}_technique_m\d{2}\.mp4$',
        'main': r'^main_\d{3}_technique_m\d{2}\.mp4$',
        'endurance': r'^endurance_\d{2}_technique_m\d{2}\.mp4$',
        'relaxation': r'^relaxation_\d{2}_technique_m\d{2}\.mp4$'
    }
    
    return patterns

def analyze_naming_compliance(video_names, reference_df):
    """Проанализировать соответствие именования стандартам"""
    
    patterns = check_naming_patterns()
    
    results = {
        'correct': [],
        'incorrect': [],
        'missing': [],
        'extra': []
    }
    
    # Проверяем каждое видео
    for video_name in video_names:
        is_valid = False
        
        for category, pattern in patterns.items():
            if re.match(pattern, video_name):
                is_valid = True
                results['correct'].append({
                    'filename': video_name,
                    'category': category,
                    'pattern': pattern
                })
                break
        
        if not is_valid:
            results['incorrect'].append({
                'filename': video_name,
                'reason': 'Не соответствует паттерну именования'
            })
    
    # Проверяем недостающие видео из эталонной таблицы
    reference_names = set()
    for _, row in reference_df.iterrows():
        reference_names.add(row['new_name'])
    
    # Находим недостающие
    missing = reference_names - video_names
    for missing_name in missing:
        results['missing'].append({
            'filename': missing_name,
            'reason': 'Отсутствует в папке exercises'
        })
    
    # Находим лишние
    extra = video_names - reference_names
    for extra_name in extra:
        results['extra'].append({
            'filename': extra_name,
            'reason': 'Не найдено в эталонной таблице'
        })
    
    return results

def generate_comparison_report(video_names, reference_names, reference_df, results):
    """Создать отчет о сравнении названий"""
    
    report = f"""# 📊 ОТЧЕТ О СООТВЕТСТВИИ НАЗВАНИЙ ВИДЕОФАЙЛОВ

## Дата: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 СВОДКА:

### Общие цифры:
- **Эталонных названий**: {len(reference_names)}
- **Фактических видео**: {len(video_names)}
- **Соответствует стандарту**: {len(results['correct'])}
- **Не соответствует стандарту**: {len(results['incorrect'])}
- **Отсутствует**: {len(results['missing'])}
- **Лишних**: {len(results['extra'])}

---

## ✅ ПРАВИЛЬНЫЕ НАЗВАНИЯ ({len(results['correct'])}):

"""
    
    if results['correct']:
        for item in results['correct'][:20]:  # Показываем первые 20
            report += f"- `{item['filename']}` - {item['category']}\n"
        
        if len(results['correct']) > 20:
            report += f"- ... и еще {len(results['correct']) - 20} файлов\n"
    else:
        report += "Нет правильно названных файлов.\n"
    
    report += f"""
---

## ❌ НЕПРАВИЛЬНЫЕ НАЗВАНИЯ ({len(results['incorrect'])}):

"""
    
    if results['incorrect']:
        for item in results['incorrect']:
            report += f"- `{item['filename']}` - {item['reason']}\n"
    else:
        report += "Все названия соответствуют стандартам.\n"
    
    report += f"""
---

## 🔍 ОТСУТСТВУЮЩИЕ ВИДЕО ({len(results['missing'])}):

"""
    
    if results['missing']:
        for item in results['missing'][:20]:  # Показываем первые 20
            report += f"- `{item['filename']}` - {item['reason']}\n"
        
        if len(results['missing']) > 20:
            report += f"- ... и еще {len(results['missing']) - 20} файлов\n"
    else:
        report += "Все эталонные видео присутствуют.\n"
    
    report += f"""
---

## 🔄 ЛИШНИЕ ВИДЕО ({len(results['extra'])}):

"""
    
    if results['extra']:
        for item in results['extra'][:20]:  # Показываем первые 20
            report += f"- `{item['filename']}` - {item['reason']}\n"
        
        if len(results['extra']) > 20:
            report += f"- ... и еще {len(results['extra']) - 20} файлов\n"
    else:
        report += "Нет лишних видео.\n"
    
    report += f"""
---

## 📋 ПАТТЕРНЫ ИМЕНОВАНИЯ:

### Ожидаемые форматы:
- **Разминка**: `warmup_NN_technique_mMM.mp4` (где NN = 01-42, MM = 01-03)
- **Основная**: `main_NNN_technique_mMM.mp4` (где NNN = 001-145, MM = 01-03)
- **Выносливость**: `endurance_NN_technique_mMM.mp4` (где NN = 01-42, MM = 01-03)
- **Расслабление**: `relaxation_NN_technique_mMM.mp4` (где NN = 01-42, MM = 01-03)

### Анализ категорий:

"""
    
    # Подсчитываем по категориям
    category_counts = {}
    for item in results['correct']:
        category = item['category']
        category_counts[category] = category_counts.get(category, 0) + 1
    
    expected_counts = {
        'warmup': 42,
        'main': 145,
        'endurance': 42,
        'relaxation': 42
    }
    
    for category, expected in expected_counts.items():
        actual = category_counts.get(category, 0)
        status = "✅" if actual == expected else "❌"
        report += f"- **{category.title()}**: {actual}/{expected} {status}\n"
    
    report += f"""
---

## 🎯 РЕКОМЕНДАЦИИ:

"""
    
    if results['incorrect']:
        report += "1. **Переименовать неправильные файлы** согласно стандартам именования\n"
    
    if results['missing']:
        report += "2. **Добавить отсутствующие видео** из источников\n"
    
    if results['extra']:
        report += "3. **Проверить лишние файлы** - возможно, они дублируют существующие\n"
    
    if not (results['incorrect'] or results['missing'] or results['extra']):
        report += "🎉 **Все названия соответствуют стандартам! Система готова к использованию.**\n"
    
    return report

def main():
    """Основная функция проверки названий"""
    
    print("🔍 ПРОВЕРКА СООТВЕТСТВИЯ НАЗВАНИЙ ВИДЕОФАЙЛОВ")
    print("=" * 60)
    
    # 1. Загружаем эталонные названия
    print("\n📋 Шаг 1: Загрузка эталонных названий...")
    reference_names, reference_df = load_reference_names()
    
    if not reference_names:
        print("❌ Не удалось загрузить эталонные названия!")
        return
    
    # 2. Получаем фактические названия
    print("\n📁 Шаг 2: Получение фактических названий видео...")
    video_names = get_actual_video_names()
    
    if not video_names:
        print("❌ Не удалось получить фактические названия видео!")
        return
    
    # 3. Анализируем соответствие
    print("\n🔍 Шаг 3: Анализ соответствия названий...")
    results = analyze_naming_compliance(video_names, reference_df)
    
    # 4. Выводим краткую статистику
    print(f"\n📊 КРАТКАЯ СТАТИСТИКА:")
    print(f"  Эталонных названий: {len(reference_names)}")
    print(f"  Фактических видео: {len(video_names)}")
    print(f"  Правильных: {len(results['correct'])} ✅")
    print(f"  Неправильных: {len(results['incorrect'])} ❌")
    print(f"  Отсутствующих: {len(results['missing'])} 🔍")
    print(f"  Лишних: {len(results['extra'])} 🔄")
    
    # 5. Создаем детальный отчет
    print("\n📄 Шаг 4: Создание детального отчета...")
    report = generate_comparison_report(video_names, reference_names, reference_df, results)
    
    # Сохраняем отчет
    report_file = '/Users/alexbel/Desktop/AI Fitness Coach/media_lists/VIDEO_NAMES_COMPLIANCE_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Отчет сохранен: {report_file}")
    
    # Итог
    print("\n" + "=" * 60)
    if results['incorrect'] or results['missing'] or results['extra']:
        print("⚠️ ВНИМАНИЕ! Обнаружены несоответствия в названиях файлов")
        print("📄 Проверьте детальный отчет для исправления")
    else:
        print("🎉 ОТЛИЧНО! Все названия соответствуют стандартам")
    
    print(f"📊 Соответствие: {len(results['correct'])}/{len(reference_names)} ({len(results['correct'])/len(reference_names)*100:.1f}%)")

if __name__ == '__main__':
    main()