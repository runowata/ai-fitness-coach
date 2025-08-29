from django.core.management.base import BaseCommand
from django.conf import settings
from apps.workouts.models import R2Video
import requests, random

class Command(BaseCommand):
    help = "Quick R2 smoke-check: prints env and HEAD 3 random video URLs"

    def handle(self, *args, **options):
        print("USE_R2_STORAGE:", getattr(settings, "USE_R2_STORAGE", None))
        print("R2_ENDPOINT:", getattr(settings, "R2_ENDPOINT", None))
        print("R2_BUCKET:", getattr(settings, "R2_BUCKET", None))
        print("R2_PUBLIC_BASE_URL:", getattr(settings, "R2_PUBLIC_BASE_URL", None))
        print("AWS_S3_ENDPOINT_URL:", getattr(settings, "AWS_S3_ENDPOINT_URL", None))
        print("AWS_STORAGE_BUCKET_NAME:", getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))

        qs = R2Video.objects.order_by("?")[:3]
        if not qs:
            print("No R2Video rows yet.")
            return

        for vc in qs:
            url = vc.get_r2_url()
            print("Clip#", vc.id, "→", url)
            try:
                r = requests.head(url, timeout=8, allow_redirects=True)
                print("HEAD:", r.status_code)
            except Exception as e:
                print("HEAD error:", e)