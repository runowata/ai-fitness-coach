#!/usr/bin/env python3
"""
Alternative script to configure R2 public access via Custom Domain
Since R2 doesn't support bucket policies, we need to:
1. Check current R2 configuration
2. Set up public access via R2 Custom Domain settings
"""
import json
import os
import sys
import boto3
from botocore.client import Config
import requests

def main():
    print("🔍 Cloudflare R2 Public Access Setup")
    print("=" * 50)
    
    # Get credentials
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("❌ Нет AWS credentials")
        sys.exit(1)
    
    # R2 configuration
    bucket_name = 'ai-fitness-media'
    endpoint_url = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
    public_domain = 'https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev'
    
    try:
        # Create S3 client for R2
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            config=Config(signature_version='s3v4')
        )
        
        print(f"🔧 Проверяем bucket: {bucket_name}")
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print("✅ Bucket найден")
        except Exception as e:
            print(f"❌ Ошибка доступа к bucket: {e}")
            sys.exit(1)
        
        # List some files to verify access
        print("\n📁 Проверяем файлы в photos/progress/:")
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='photos/progress/',
                MaxKeys=5
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    print(f"   📄 {obj['Key']}")
            else:
                print("   ⚠️  Файлы не найдены в photos/progress/")
        except Exception as e:
            print(f"❌ Ошибка при просмотре файлов: {e}")
        
        # Test public access to known image
        print(f"\n🧪 Тестируем публичный доступ:")
        test_url = f"{public_domain}/photos/progress/card_progress_0066.jpg"
        print(f"URL: {test_url}")
        
        try:
            response = requests.head(test_url, timeout=10)
            print(f"Статус: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ УСПЕХ! Публичный доступ работает")
                print("🎉 Изображения должны отображаться в приложении")
            elif response.status_code == 401:
                print("❌ 401 Unauthorized - публичный доступ не настроен")
                print("\n💡 Решение:")
                print("1. Зайти в Cloudflare Dashboard")
                print("2. R2 Object Storage → ai-fitness-media")
                print("3. Settings → Public access → Allow Access")
                print("4. Или настроить Custom Domain с публичным доступом")
            elif response.status_code == 404:
                print("❌ 404 Not Found - файл не существует")
            else:
                print(f"⚠️  Неожиданный статус: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса: {e}")
        
        print("\n" + "=" * 50)
        print("📚 Дополнительная информация:")
        print("- R2 не поддерживает bucket policies как AWS S3")
        print("- Нужно использовать настройки публичного доступа в Cloudflare Dashboard")
        print("- Или настроить Custom Domain для публичных файлов")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()