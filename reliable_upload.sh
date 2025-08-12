#!/bin/bash
# reliable_upload.sh
# Надёжная загрузка с автоматическим перезапуском при сбоях

LOG_FILE="r2_upload_reliable.log"
STATE_FILE="r2_upload_state.json"
MAX_RETRIES=100
TIMEOUT_MINUTES=30

echo "🛡️ Надёжная загрузка в R2 с автоматическим восстановлением"
echo "==========================================================="
echo "• Автоперезапуск при сбоях: ДА"
echo "• Таймаут на попытку: ${TIMEOUT_MINUTES} минут"
echo "• Максимум попыток: ${MAX_RETRIES}"
echo "• Лог: ${LOG_FILE}"
echo ""

# Функция для получения количества загруженных файлов
get_uploaded_count() {
    if [ -f "$STATE_FILE" ]; then
        python -c "import json; print(len(json.load(open('$STATE_FILE'))))"
    else
        echo "0"
    fi
}

# Функция для получения общего количества файлов
get_total_count() {
    python -c "from pathlib import Path; print(sum(1 for _ in Path('selected_media').rglob('*') if _.is_file()))"
}

TOTAL_FILES=$(get_total_count)
RETRY_COUNT=0
LAST_UPLOADED=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    CURRENT_UPLOADED=$(get_uploaded_count)
    REMAINING=$((TOTAL_FILES - CURRENT_UPLOADED))
    
    echo "📊 Статус: Загружено $CURRENT_UPLOADED из $TOTAL_FILES файлов"
    
    # Проверяем, все ли файлы загружены
    if [ $REMAINING -eq 0 ]; then
        echo "🎉 Все файлы успешно загружены!"
        break
    fi
    
    # Проверяем, был ли прогресс с прошлой попытки
    if [ $CURRENT_UPLOADED -gt $LAST_UPLOADED ]; then
        echo "✅ Прогресс: +$((CURRENT_UPLOADED - LAST_UPLOADED)) файлов"
        RETRY_COUNT=0  # Сбрасываем счётчик неудачных попыток
    else
        if [ $RETRY_COUNT -gt 0 ]; then
            echo "⚠️  Нет прогресса, попытка $((RETRY_COUNT + 1)) из $MAX_RETRIES"
        fi
    fi
    
    LAST_UPLOADED=$CURRENT_UPLOADED
    
    echo "🔄 Запуск загрузки (осталось: $REMAINING файлов)..."
    echo "---" >> $LOG_FILE
    echo "[$(date)] Попытка $((RETRY_COUNT + 1)), осталось: $REMAINING файлов" >> $LOG_FILE
    
    # Запускаем загрузку с таймаутом (используем gtimeout на macOS или встроенный механизм)
    if command -v gtimeout &> /dev/null; then
        gtimeout ${TIMEOUT_MINUTES}m python upload_to_r2.py --auto >> $LOG_FILE 2>&1
    elif command -v timeout &> /dev/null; then
        timeout ${TIMEOUT_MINUTES}m python upload_to_r2.py --auto >> $LOG_FILE 2>&1
    else
        # Fallback - запускаем без timeout
        python upload_to_r2.py --auto >> $LOG_FILE 2>&1 &
        PID=$!
        SECONDS=0
        MAX_SECONDS=$((TIMEOUT_MINUTES * 60))
        
        while kill -0 $PID 2>/dev/null; do
            if [ $SECONDS -ge $MAX_SECONDS ]; then
                echo "⏱️  Таймаут через ${TIMEOUT_MINUTES} минут, останавливаем процесс..."
                kill $PID 2>/dev/null
                wait $PID 2>/dev/null
                break
            fi
            sleep 10
        done
    fi
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⏱️  Таймаут через ${TIMEOUT_MINUTES} минут, перезапуск..."
    elif [ $EXIT_CODE -ne 0 ]; then
        echo "❌ Ошибка (код: $EXIT_CODE), перезапуск через 10 секунд..."
        sleep 10
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # Небольшая пауза между попытками
    sleep 5
done

# Финальная проверка
FINAL_UPLOADED=$(get_uploaded_count)
FINAL_REMAINING=$((TOTAL_FILES - FINAL_UPLOADED))

echo ""
echo "==========================================================="
echo "📊 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:"
echo "• Загружено: $FINAL_UPLOADED из $TOTAL_FILES файлов"
echo "• Осталось: $FINAL_REMAINING файлов"

if [ $FINAL_REMAINING -eq 0 ]; then
    echo "✅ Статус: УСПЕШНО ЗАВЕРШЕНО"
    
    # Показываем примеры URL
    echo ""
    echo "🔗 Примеры URL для доступа:"
    echo "• https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com/videos/exercises/squats_technique_m01.mp4"
    echo "• https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/quotes/card_quotes_0001.jpg"
else
    echo "⚠️  Статус: НЕ ВСЕ ФАЙЛЫ ЗАГРУЖЕНЫ"
    echo "Запустите скрипт повторно для продолжения"
fi

echo "📝 Полный лог: $LOG_FILE"