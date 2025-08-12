#!/bin/bash
# auto_upload_r2.sh
# Автоматически перезапускает загрузку до полного завершения

echo "🚀 Автоматическая загрузка в R2 с перезапуском"
echo "=============================================="

while true; do
    echo ""
    echo "📊 Проверка прогресса..."
    python check_upload_progress.py
    
    # Проверяем, есть ли еще файлы для загрузки
    remaining=$(python -c "
import json
from pathlib import Path
state_file = Path('r2_upload_state.json')
media_dir = Path('selected_media')
total = sum(1 for _ in media_dir.rglob('*') if _.is_file())
uploaded = len(json.load(open(state_file))) if state_file.exists() else 0
print(total - uploaded)
")
    
    if [ "$remaining" -eq "0" ]; then
        echo "🎉 Все файлы загружены!"
        break
    fi
    
    echo ""
    echo "⏳ Осталось файлов: $remaining"
    echo "🔄 Запускаем загрузку..."
    
    # Запускаем загрузку с таймаутом 30 минут
    timeout 1800 python upload_to_r2.py --auto
    
    # Небольшая пауза между попытками
    echo "⏸️  Пауза 5 секунд..."
    sleep 5
done

echo ""
echo "✅ Загрузка завершена!"
echo ""
python check_upload_progress.py