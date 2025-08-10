#!/usr/bin/env python3
"""
Script to apply R2 bucket policy for public access to motivational images
"""
import json
import os
import sys
import boto3
from botocore.client import Config

def main():
    # R2/AWS credentials from environment (try both R2_* and AWS_* variants)
    r2_access_key = os.getenv('R2_ACCESS_KEY_ID') or os.getenv('AWS_ACCESS_KEY_ID')
    r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not r2_access_key or not r2_secret_key:
        print("❌ Ошибка: Нужны переменные окружения для R2/AWS:")
        print("  R2_ACCESS_KEY_ID или AWS_ACCESS_KEY_ID")
        print("  R2_SECRET_ACCESS_KEY или AWS_SECRET_ACCESS_KEY")
        print()
        print("Доступные переменные:")
        aws_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        print(f"  AWS_ACCESS_KEY_ID: {'✓ найден' if aws_key else '✗ не найден'}")
        print(f"  AWS_SECRET_ACCESS_KEY: {'✓ найден' if aws_secret else '✗ не найден'}")
        sys.exit(1)
    
    # R2 configuration
    bucket_name = 'ai-fitness-media'
    endpoint_url = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
    
    # Bucket policy
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadMotivationalImages",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/photos/progress/*"
            }
        ]
    }
    
    try:
        # Create S3 client for R2
        s3_client = boto3.client(
            's3',
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            endpoint_url=endpoint_url,
            config=Config(signature_version='s3v4')
        )
        
        print(f"🔧 Применяем bucket policy к {bucket_name}...")
        print("📋 Policy содержание:")
        print(json.dumps(bucket_policy, indent=2))
        print()
        
        # Apply bucket policy
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        
        print("✅ Bucket policy успешно применен!")
        print()
        print("🧪 Тестируем доступ...")
        
        # Test access to a known image
        test_url = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev/photos/progress/card_progress_0066.jpg"
        print(f"curl -I {test_url}")
        
        import requests
        response = requests.head(test_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ УСПЕХ! Изображения теперь доступны публично")
        else:
            print(f"⚠️  Получен статус {response.status_code}")
            print("Возможно, нужно подождать несколько минут для применения политики")
        
    except Exception as e:
        print(f"❌ Ошибка при применении bucket policy: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()