#!/usr/bin/env python3
"""
check_upload_progress.py
------------------------
Проверяет прогресс загрузки в R2.
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.cwd()
SELECTED_MEDIA = PROJECT_ROOT / "selected_media"
UPLOAD_STATE = PROJECT_ROOT / "r2_upload_state.json"

def check_progress():
    print("📊 Прогресс загрузки в Cloudflare R2")
    print("=" * 60)
    
    # Считаем общее количество файлов
    total_files = sum(1 for _ in SELECTED_MEDIA.rglob('*') if _.is_file())
    
    # Загружаем состояние
    if UPLOAD_STATE.exists():
        with open(UPLOAD_STATE, 'r') as f:
            uploaded_files = json.load(f)
        uploaded_count = len(uploaded_files)
    else:
        uploaded_count = 0
        uploaded_files = []
    
    remaining = total_files - uploaded_count
    percent = (uploaded_count / total_files) * 100 if total_files > 0 else 0
    
    print(f"📁 Всего файлов:     {total_files}")
    print(f"✅ Загружено:        {uploaded_count}")
    print(f"⏳ Осталось:         {remaining}")
    print(f"📈 Прогресс:         {percent:.1f}%")
    
    # Прогресс-бар
    bar_length = 50
    filled = int(bar_length * uploaded_count / total_files)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\n[{bar}] {percent:.1f}%")
    
    # Статистика по категориям
    print("\n📂 По категориям:")
    print("-" * 60)
    
    categories = {}
    for file_key in uploaded_files:
        category = file_key.split('/')[0] if '/' in file_key else 'root'
        categories[category] = categories.get(category, 0) + 1
    
    for cat, count in sorted(categories.items()):
        print(f"  {cat:<20} {count:>10} файлов")
    
    # Оценка времени
    if uploaded_count > 0 and remaining > 0:
        # Предполагаем среднюю скорость ~10 файлов/минуту
        minutes_remaining = remaining / 10
        hours = int(minutes_remaining // 60)
        minutes = int(minutes_remaining % 60)
        
        print("\n⏱️  Примерное время до завершения:")
        if hours > 0:
            print(f"   ~{hours}ч {minutes}мин")
        else:
            print(f"   ~{minutes}мин")
    
    print("\n" + "=" * 60)
    
    if remaining > 0:
        print("💡 Для продолжения загрузки запустите:")
        print("   python upload_to_r2.py --auto")
    else:
        print("🎉 Все файлы загружены!")

if __name__ == "__main__":
    check_progress()