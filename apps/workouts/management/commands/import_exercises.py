import ast
from csv import DictReader
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.workouts.models import CSVExercise

CSV_PATH = Path("data/clean/exercises.csv")


class Command(BaseCommand):
    help = "Импортирует упражнения из data/clean/exercises.csv"

    def handle(self, *args, **kwargs):
        if not CSV_PATH.exists():
            raise CommandError(f"{CSV_PATH} not found")

        created, updated = 0, 0
        with CSV_PATH.open(encoding="utf-8") as f:
            for row in DictReader(f):
                # Strict validation - fail fast on bad data
                if not row.get("id") or row["id"].strip() == "":
                    raise ValueError(f"Blank ID in CSV at row {created + updated + 1} — must be filled")
                
                # Check for duplicates in current import
                if CSVExercise.objects.filter(id=row["id"]).exists() and created > 0:
                    raise ValueError(f"Duplicate ID {row['id']} in CSV — fix source file")
                
                # Парсим AI tags из строки в список
                ai_tags_str = row.get("ai_tags", "")
                try:
                    # Пробуем парсить как список Python
                    if ai_tags_str.startswith('[') and ai_tags_str.endswith(']'):
                        ai_tags = ast.literal_eval(ai_tags_str)
                    else:
                        # Если не список, разделяем по запятым
                        ai_tags = [t.strip() for t in ai_tags_str.split(",") if t.strip()]
                except:
                    ai_tags = [t.strip() for t in ai_tags_str.split(",") if t.strip()]
                
                obj, is_created = CSVExercise.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "name_ru": row["name_ru"],
                        "name_en": row["name_en"],
                        "level": row["level"],
                        "description": row.get("description", ""),
                        "muscle_group": row.get("muscle_group", ""),
                        "exercise_type": row.get("exercise_type", ""),
                        "ai_tags": ai_tags,
                    },
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Created: {created}, Updated: {updated}"))