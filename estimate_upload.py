#!/usr/bin/env python3
"""
estimate_upload.py
-----------------
Оценивает размер и время загрузки медиатеки в R2.
"""

from pathlib import Path
from collections import defaultdict
import time

PROJECT_ROOT = Path.cwd()
SELECTED_MEDIA = PROJECT_ROOT / "selected_media"

def estimate():
    print("📊 Анализ медиатеки для загрузки в R2")
    print("=" * 60)
    
    if not SELECTED_MEDIA.exists():
        print(f"❌ Папка {SELECTED_MEDIA} не найдена")
        return
    
    # Собираем статистику
    stats = defaultdict(lambda: {'count': 0, 'size': 0})
    total_size = 0
    total_count = 0
    
    print("Сканирование файлов...")
    for file_path in SELECTED_MEDIA.rglob('*'):
        if file_path.is_file():
            size = file_path.stat().st_size
            category = str(file_path.relative_to(SELECTED_MEDIA).parts[0])
            
            stats[category]['count'] += 1
            stats[category]['size'] += size
            total_size += size
            total_count += 1
    
    # Выводим статистику
    print("\n📁 Статистика по категориям:")
    print("-" * 60)
    print(f"{'Категория':<20} {'Файлов':>10} {'Размер':>15}")
    print("-" * 60)
    
    for category in sorted(stats.keys()):
        count = stats[category]['count']
        size_gb = stats[category]['size'] / (1024**3)
        print(f"{category:<20} {count:>10} {size_gb:>14.2f} GB")
    
    print("-" * 60)
    total_gb = total_size / (1024**3)
    print(f"{'ИТОГО':<20} {total_count:>10} {total_gb:>14.2f} GB")
    
    # Оценка времени загрузки
    print("\n⏱️  Оценка времени загрузки:")
    print("-" * 60)
    
    speeds = {
        "Медленное соединение (5 Mbps)": 5 * 1024 * 1024 / 8,  # байт/сек
        "Среднее соединение (25 Mbps)": 25 * 1024 * 1024 / 8,
        "Быстрое соединение (100 Mbps)": 100 * 1024 * 1024 / 8,
        "Гигабит (500 Mbps реальная)": 500 * 1024 * 1024 / 8,
    }
    
    for speed_name, speed_bytes in speeds.items():
        time_seconds = total_size / speed_bytes
        hours = int(time_seconds // 3600)
        minutes = int((time_seconds % 3600) // 60)
        
        if hours > 0:
            time_str = f"{hours}ч {minutes}мин"
        else:
            time_str = f"{minutes}мин"
        
        print(f"{speed_name:<30} ~{time_str}")
    
    # Стоимость хранения в R2
    print("\n💰 Стоимость хранения в Cloudflare R2:")
    print("-" * 60)
    
    # R2 pricing: $0.015 per GB per month
    monthly_cost = total_gb * 0.015
    yearly_cost = monthly_cost * 12
    
    print(f"Месяц:  ${monthly_cost:.2f}")
    print(f"Год:    ${yearly_cost:.2f}")
    print("\n📝 Примечание: Исходящий трафик в R2 бесплатный!")
    
    # Рекомендации
    print("\n💡 Рекомендации:")
    print("-" * 60)
    
    if total_gb > 100:
        print("• Размер > 100GB - рекомендуется загружать ночью")
        print("• Используйте скрипт upload_to_r2.py с возможностью докачки")
    
    if total_count > 5000:
        print(f"• Много файлов ({total_count}) - загрузка может занять время")
        print("• Скрипт использует 5 параллельных потоков для ускорения")
    
    print("• После загрузки обязательно сохраните r2_upload_state.json")
    print("• Это позволит докачать файлы при прерывании")
    
    print("\n" + "=" * 60)
    print("Готово к загрузке! Запустите: python upload_to_r2.py")

if __name__ == "__main__":
    estimate()