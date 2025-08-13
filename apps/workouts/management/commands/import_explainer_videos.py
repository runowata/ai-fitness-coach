from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from slugify import slugify

from apps.workouts.models import CSVExercise, ExplainerVideo

RAW_DIR = Path("data/raw")

ARCHETYPE_MAP = {
    "111": "nastavnik",
    "222": "professional", 
    "333": "rovesnik",
}

class Command(BaseCommand):
    help = "Импортирует скрипты видео-объяснений по архетипам"

    def handle(self, *args, **kwargs):
        created, updated = 0, 0

        for code, suffix in ARCHETYPE_MAP.items():
            fn = RAW_DIR / f"explainer_videos_{code}_{suffix}.xlsx"
            if not fn.exists():
                self.stdout.write(self.style.WARNING(f"Skip {fn.name} (not found)"))
                continue

            self.stdout.write(f"Processing {fn.name}...")
            df = pd.read_excel(fn)
            
            # Приводим названия колонок к стандартному виду
            df.columns = [slugify(c, separator="_") for c in df.columns]
            
            # Показываем какие колонки нашли
            self.stdout.write(f"  Found columns: {list(df.columns)}")
            
            # Определяем нужные колонки
            id_col = None
            script_col = None
            
            for col in df.columns:
                if 'id' in col.lower():
                    id_col = col
                if 'skript' in col or 'script' in col:
                    script_col = col
                    
            if not id_col or not script_col:
                self.stdout.write(self.style.ERROR(f"  Missing required columns in {fn.name}"))
                continue
                
            self.stdout.write(f"  Using ID column: {id_col}")
            self.stdout.write(f"  Using script column: {script_col}")

            for _, row in df.iterrows():
                exercise_id = row[id_col]
                script_text = row[script_col]
                
                # Пропускаем пустые строки
                if pd.isna(exercise_id) or pd.isna(script_text):
                    continue
                
                # Проверяем, что упражнение существует
                if not CSVExercise.objects.filter(id=exercise_id).exists():
                    self.stdout.write(self.style.WARNING(f"  Exercise {exercise_id} not found, skipping"))
                    continue
                    
                obj, is_created = ExplainerVideo.objects.update_or_create(
                    exercise_id=exercise_id,
                    archetype=code,
                    locale="ru",  # Пока только русский
                    defaults={"script": script_text},
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Created: {created}, Updated: {updated}"))