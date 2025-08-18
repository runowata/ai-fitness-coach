#!/usr/bin/env python3
"""
Простая загрузка на Cloudflare R2
"""

import boto3
from botocore.exceptions import NoCredentialsError

# Конфигурация
access_key = '3a9fd5a6b38ec994e057e33c1096874e'
secret_key = '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
endpoint_url = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
bucket_name = 'ai-fitness-media'

print("🚀 Простая загрузка на R2")
print(f"📡 Endpoint: {endpoint_url}")
print(f"🪣 Bucket: {bucket_name}")

# Создаем клиента без дополнительных настроек
s3 = boto3.client(
    's3',
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
)

# Пробуем создать тестовый файл
test_content = b"Test upload to R2"
test_key = "test.txt"

try:
    print(f"\n📤 Загружаем тестовый файл: {test_key}")
    s3.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=test_content
    )
    print("✅ Тестовый файл загружен успешно!")
    
    # Проверяем, что файл существует
    response = s3.head_object(Bucket=bucket_name, Key=test_key)
    print(f"✅ Файл проверен, размер: {response['ContentLength']} байт")
    
    # Удаляем тестовый файл
    s3.delete_object(Bucket=bucket_name, Key=test_key)
    print("🗑️ Тестовый файл удален")
    
    print("\n🎉 ПОДКЛЮЧЕНИЕ РАБОТАЕТ! Можно загружать видео.")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    print("\n🔍 Детали ошибки:")
    import traceback
    traceback.print_exc()