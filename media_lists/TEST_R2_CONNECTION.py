#!/usr/bin/env python3
"""
Тестирование подключения к Cloudflare R2
"""

import boto3
from botocore.config import Config

# Тестируем разные конфигурации
configs = [
    {
        'name': 'Endpoint из переменных',
        'endpoint_url': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
        'region': 'auto'
    },
    {
        'name': 'Cloudflare общий endpoint',
        'endpoint_url': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
        'region': 'us-east-1'
    },
    {
        'name': 'Без региона',
        'endpoint_url': 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com',
        'region': None
    }
]

credentials = {
    'access_key': '3a9fd5a6b38ec994e057e33c1096874e',
    'secret_key': '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa1'
}

bucket_name = 'ai-fitness-media'

for config in configs:
    print(f"\n🔄 Тестируем: {config['name']}")
    print(f"  Endpoint: {config['endpoint_url']}")
    print(f"  Region: {config['region']}")
    
    try:
        # Создаем конфигурацию
        s3_config = Config(
            region_name=config['region'],
            s3={'addressing_style': 'path'}
        ) if config['region'] else Config(s3={'addressing_style': 'path'})
        
        # Создаем клиент
        s3_client = boto3.client(
            's3',
            endpoint_url=config['endpoint_url'],
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_key'],
            config=s3_config
        )
        
        # Тестируем список объектов
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print(f"  ✅ Успех! Найдено объектов: {response.get('KeyCount', 0)}")
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

print("\n" + "="*50)
print("🔍 Попробуем через публичный URL...")

# Тестируем публичный доступ
import requests

public_url = "https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev"
test_file = "videos/exercises/warmup_01_technique_m01.mp4"  # Если файл существует

try:
    response = requests.head(f"{public_url}/{test_file}", timeout=10)
    print(f"✅ Публичный URL работает: {response.status_code}")
except Exception as e:
    print(f"❌ Публичный URL недоступен: {e}")

print("\n📝 Рекомендации:")
print("1. Проверьте актуальность ключей доступа в Cloudflare Dashboard")
print("2. Убедитесь, что bucket настроен правильно")
print("3. Проверьте права доступа для API токенов")
print("4. Возможно, нужно использовать другой region или endpoint")