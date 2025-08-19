from django.core.management.base import BaseCommand
from django.core.cache import caches

class Command(BaseCommand):
    help = "Check Redis cache availability (or fallback cache)"

    def handle(self, *args, **options):
        cache = caches["default"]
        try:
            cache.set("redis_check_key", "ok", 5)
            val = cache.get("redis_check_key")
            if val == "ok":
                self.stdout.write(self.style.SUCCESS("Redis cache OK"))
            else:
                self.stdout.write(self.style.WARNING("Cache set/get mismatch (likely fallback)"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Redis cache ERROR: {e}"))
            raise SystemExit(1)