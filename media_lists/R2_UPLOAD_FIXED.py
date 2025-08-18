#!/usr/bin/env python3
"""
Загрузка на Cloudflare R2 с исправлениями
"""

import boto3
from botocore.config import Config
import os

# Конфигурация R2 - используем точные значения из переменных окружения
config = {
    'access_key': '3a9fd5a6b38ec994e057e33c1096874e',
    'secret_key': '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa1',
    'endpoint': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
    'bucket': 'ai-fitness-media',
    'public_url': 'https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev'
}

print("🚀 Загрузка на Cloudflare R2")
print(f"📡 Endpoint: {config['endpoint']}")
print(f"🪣 Bucket: {config['bucket']}")

# Создаем клиента с правильными настройками для R2
# R2 использует AWS Signature Version 4
s3_config = Config(
    signature_version='s3v4',
    region_name='us-east-1'  # R2 ожидает us-east-1 или auto
)

try:
    s3_client = boto3.client(
        's3',
        endpoint_url=config['endpoint'],
        aws_access_key_id=config['access_key'],
        aws_secret_access_key=config['secret_key'],
        config=s3_config
    )
    
    # Тестируем подключение
    print("\n🔄 Тестируем подключение...")
    
    # Создаем тестовый файл
    test_content = b"Test upload to Cloudflare R2"
    test_key = "test_upload.txt"
    
    print(f"📤 Загружаем тестовый файл: {test_key}")
    
    response = s3_client.put_object(
        Bucket=config['bucket'],
        Key=test_key,
        Body=test_content,
        ContentType='text/plain'
    )
    
    print(f"✅ Файл загружен! ETag: {response.get('ETag', 'N/A')}")
    
    # Проверяем доступность через публичный URL
    public_file_url = f"{config['public_url']}/{test_key}"
    print(f"🌐 Публичный URL: {public_file_url}")
    
    # Удаляем тестовый файл
    s3_client.delete_object(Bucket=config['bucket'], Key=test_key)
    print("🗑️ Тестовый файл удален")
    
    print("\n✅ ПОДКЛЮЧЕНИЕ РАБОТАЕТ!")
    print("Можно загружать видео!")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    
    # Пробуем альтернативный подход
    print("\n🔄 Пробуем альтернативный подход без региона...")
    
    try:
        s3_client_alt = boto3.client(
            's3',
            endpoint_url=config['endpoint'],
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            region_name='auto',
            use_ssl=True
        )
        
        response = s3_client_alt.put_object(
            Bucket=config['bucket'],
            Key='test2.txt',
            Body=b'Test 2'
        )
        
        print("✅ Альтернативный подход работает!")
        s3_client_alt.delete_object(Bucket=config['bucket'], Key='test2.txt')
        
    except Exception as e2:
        print(f"❌ Альтернативный подход тоже не работает: {e2}")