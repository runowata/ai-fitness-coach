#!/bin/bash

# Установка переменных окружения
export AWS_ACCESS_KEY_ID="3a9fd5a6b38ec994e057e33c1096874e"
export AWS_SECRET_ACCESS_KEY="0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa1"
export AWS_DEFAULT_REGION="auto"

ENDPOINT_URL="https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com"
BUCKET="ai-fitness-media"

echo "🔄 Тестируем подключение к R2..."
echo "📡 Endpoint: $ENDPOINT_URL"
echo "🪣 Bucket: $BUCKET"

# Создаем тестовый файл
echo "Test R2 upload" > /tmp/test_r2.txt

# Пробуем загрузить
echo "📤 Загружаем тестовый файл..."
aws s3 cp /tmp/test_r2.txt s3://$BUCKET/test.txt --endpoint-url=$ENDPOINT_URL

# Проверяем результат
if [ $? -eq 0 ]; then
    echo "✅ Файл загружен успешно!"
    
    # Проверяем список файлов
    echo "📋 Проверяем список файлов..."
    aws s3 ls s3://$BUCKET/ --endpoint-url=$ENDPOINT_URL
    
    # Удаляем тестовый файл
    echo "🗑️ Удаляем тестовый файл..."
    aws s3 rm s3://$BUCKET/test.txt --endpoint-url=$ENDPOINT_URL
else
    echo "❌ Ошибка загрузки"
fi

# Удаляем временный файл
rm /tmp/test_r2.txt