#!/usr/bin/env python
"""
Check R2 storage contents
"""
import boto3
from collections import defaultdict

# Cloudflare R2 credentials
ACCESS_KEY_ID = '3a9fd5a6b38ec994e057e33c1096874e'
SECRET_ACCESS_KEY = '0817f9a3154b63b1968620a966e05e36f80fca0308ba91d9c8bf65e8622baa13'
ENDPOINT_URL = 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com'
BUCKET_NAME = 'ai-fitness-media'

# Create S3 client for R2
s3_client = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name='auto'
)

def list_all_files():
    """List all files in R2 bucket"""
    try:
        # Get all objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_NAME)
        
        files_by_category = defaultdict(list)
        total_count = 0
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    size = obj['Size']
                    
                    # Categorize by directory
                    parts = key.split('/')
                    if len(parts) > 1:
                        category = parts[0]
                    else:
                        category = 'root'
                    
                    files_by_category[category].append(key)
                    total_count += 1
        
        # Print summary
        print(f"\n=== R2 Storage Summary ===")
        print(f"Total files: {total_count}")
        print(f"\nFiles by category:")
        
        for category in sorted(files_by_category.keys()):
            files = files_by_category[category]
            print(f"\n{category}: {len(files)} files")
            # Show first 5 files as examples
            for i, file in enumerate(files[:5]):
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
        
        # Check for motivational cards specifically
        print(f"\n=== Looking for Motivational Card Images ===")
        motivation_patterns = ['motivation', 'quotes', 'cards', 'progress', 'photos']
        found_motivation = False
        
        for pattern in motivation_patterns:
            matching = []
            for category, files in files_by_category.items():
                if pattern in category.lower():
                    matching.extend(files)
                else:
                    for file in files:
                        if pattern in file.lower():
                            matching.append(file)
            
            if matching:
                found_motivation = True
                print(f"\nFound {len(matching)} files with '{pattern}':")
                for file in matching[:5]:
                    print(f"  - {file}")
                if len(matching) > 5:
                    print(f"  ... and {len(matching) - 5} more")
        
        if not found_motivation:
            print("No motivational card images found!")
        
        return files_by_category
        
    except Exception as e:
        print(f"Error accessing R2: {e}")
        return {}

if __name__ == "__main__":
    list_all_files()