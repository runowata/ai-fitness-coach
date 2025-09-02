import os
import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check what media files are available in R2 bucket'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            choices=['avatars', 'cards', 'all'],
            default='all',
            help='Which category to check'
        )

    def handle(self, *args, **options):
        base_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
        if not base_url:
            self.stderr.write("R2_PUBLIC_URL not set")
            return

        category = options['category']
        
        # Common file patterns to check
        test_files = []
        
        if category in ['avatars', 'all']:
            test_files.extend([
                "images/avatars/peer_avatar_1.jpg",
                "images/avatars/professional_avatar_1.jpg", 
                "images/avatars/mentor_avatar_1.jpg",
                "images/avatars/peer.png",
                "images/avatars/professional.png",
                "images/avatars/mentor.png",
            ])
        
        if category in ['cards', 'all']:
            test_files.extend([
                "images/cards/card_motivation_1.jpg",
                "images/cards/card_motivation_2.jpg",
                "images/cards/card_motivation_3.jpg",
                "images/cards/bg01.jpg",
                "images/cards/bg02.jpg", 
                "images/cards/bg03.jpg",
            ])

        self.stdout.write(f"Checking R2 files at {base_url}")
        self.stdout.write("=" * 60)
        
        available = []
        missing = []
        
        for file_path in test_files:
            url = f"{base_url}/{file_path}"
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    size = response.headers.get('content-length', 'unknown')
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ {file_path} (size: {size} bytes)")
                    )
                    available.append(file_path)
                else:
                    self.stdout.write(
                        self.style.WARNING(f"❌ {file_path} (HTTP {response.status_code})")
                    )
                    missing.append(file_path)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {file_path} (Error: {e})")
                )
                missing.append(file_path)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Summary: {len(available)} available, {len(missing)} missing")
        
        if available:
            self.stdout.write("\nReady to use these files in seed_media_assets command!")
        if missing:
            self.stdout.write(f"\nMissing files need to be uploaded to R2 bucket.")