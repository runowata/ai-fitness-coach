#!/bin/bash
# monitor_upload.sh
# Мониторинг загрузки в реальном времени

echo "📊 Мониторинг загрузки в R2 (обновление каждые 30 сек)"
echo "Нажмите Ctrl+C для выхода"
echo "========================================================"

while true; do
    clear
    echo "📊 Мониторинг загрузки в R2 - $(date '+%H:%M:%S')"
    echo "========================================================"
    
    # Проверяем процесс
    if ps aux | grep -v grep | grep -q "upload_to_r2.py"; then
        echo "✅ Процесс загрузки активен"
        PID=$(ps aux | grep -v grep | grep "upload_to_r2.py" | awk '{print $2}')
        echo "   PID: $PID"
    else
        echo "⚠️  Процесс загрузки не найден"
    fi
    
    echo ""
    
    # Показываем прогресс
    python -c "
import json
from pathlib import Path

state_file = Path('r2_upload_state.json')
media_dir = Path('selected_media')

total = sum(1 for _ in media_dir.rglob('*') if _.is_file())
uploaded = len(json.load(open(state_file))) if state_file.exists() else 0
remaining = total - uploaded
percent = (uploaded / total * 100) if total > 0 else 0

print(f'📁 Всего файлов:  {total}')
print(f'✅ Загружено:     {uploaded}')
print(f'⏳ Осталось:      {remaining}')
print(f'📈 Прогресс:      {percent:.1f}%')
print()

# Прогресс-бар
bar_length = 50
filled = int(bar_length * uploaded / total)
bar = '█' * filled + '░' * (bar_length - filled)
print(f'[{bar}] {percent:.1f}%')
print()

# Скорость (если есть предыдущее состояние)
import time
state_time_file = Path('.upload_monitor_state')
current_time = time.time()

if state_time_file.exists():
    with open(state_time_file) as f:
        prev_data = f.read().split(',')
        prev_uploaded = int(prev_data[0])
        prev_time = float(prev_data[1])
    
    time_diff = current_time - prev_time
    files_diff = uploaded - prev_uploaded
    
    if time_diff > 0:
        speed = files_diff / time_diff * 60  # файлов в минуту
        if speed > 0:
            eta_minutes = remaining / speed
            eta_hours = int(eta_minutes // 60)
            eta_mins = int(eta_minutes % 60)
            print(f'⚡ Скорость:      {speed:.1f} файлов/мин')
            if eta_hours > 0:
                print(f'⏱️  Осталось:      ~{eta_hours}ч {eta_mins}мин')
            else:
                print(f'⏱️  Осталось:      ~{eta_mins}мин')

# Сохраняем текущее состояние
with open(state_time_file, 'w') as f:
    f.write(f'{uploaded},{current_time}')
"
    
    # Последние строки лога
    echo ""
    echo "📝 Последние записи лога:"
    echo "------------------------"
    if [ -f "r2_upload_continue.log" ]; then
        tail -5 r2_upload_continue.log | sed 's/^/   /'
    fi
    
    # Ждём 30 секунд
    sleep 30
done