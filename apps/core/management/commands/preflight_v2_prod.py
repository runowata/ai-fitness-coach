from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os

LEGACY_COLUMNS = {
    "video_clips": {"type", "url"},
    "exercises": {"technique_video_url", "mistake_video_url"},
}
REQUIRED_COLUMNS = {
    "video_clips": {"r2_kind", "archetype"},
}

class Command(BaseCommand):
    help = "Проверка, что прод-БД и конфиг не содержат легаси-ссылок на v1/старое хранилище."

    def handle(self, *args, **opts):
        ok = True

        # 1) env/настройки
        use_r2 = getattr(settings, "USE_R2_STORAGE", False)
        if not use_r2:
            self.stderr.write("❌ USE_R2_STORAGE=False (ожидаем True на проде)")
            ok = False
        for k in ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_ENDPOINT"]:
            if not os.getenv(k):
                self.stderr.write(f"❌ env var {k} не задан")
                ok = False

        # 2) колонки таблиц  
        with connection.cursor() as cur:
            try:
                # Try PostgreSQL first
                for table, legacy in LEGACY_COLUMNS.items():
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", [table])
                    cols = {r[0] for r in cur.fetchall()}
                    leftovers = cols & legacy
                    if leftovers:
                        self.stderr.write(f"❌ {table}: найдены легаси-колонки: {sorted(leftovers)}")
                        ok = False
                    req = REQUIRED_COLUMNS.get(table, set())
                    missing = req - cols
                    if missing:
                        self.stderr.write(f"❌ {table}: отсутствуют нужные колонки: {sorted(missing)}")
                        ok = False

                # 3) PostgreSQL индексы с упоминанием legacy-поля type
                cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='video_clips'")
                bad = [name for name, ddl in cur.fetchall() if " type " in ddl or "(type," in ddl or ", type)" in ddl]
                if bad:
                    self.stderr.write(f"❌ video_clips: индексы/уникальные ограничения с type: {bad}")
                    ok = False
                    
            except Exception:
                # Fall back to SQLite
                for table, legacy in LEGACY_COLUMNS.items():
                    cur.execute(f"PRAGMA table_info({table})")
                    cols = {row[1] for row in cur.fetchall()}  # column name is index 1
                    leftovers = cols & legacy
                    if leftovers:
                        self.stderr.write(f"❌ {table}: найдены легаси-колонки: {sorted(leftovers)}")
                        ok = False
                    req = REQUIRED_COLUMNS.get(table, set())
                    missing = req - cols
                    if missing:
                        self.stderr.write(f"❌ {table}: отсутствуют нужные колонки: {sorted(missing)}")
                        ok = False

                # 3) SQLite индексы
                cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='video_clips'")
                bad = [name for name, sql in cur.fetchall() if sql and (" type " in sql or "(type," in sql or ", type)" in sql)]
                if bad:
                    self.stderr.write(f"❌ video_clips: индексы/уникальные ограничения с type: {bad}")
                    ok = False

        # 4) prompts профайл
        prof = getattr(settings, "PROMPTS_PROFILE", None)
        if prof != "v2":
            self.stderr.write(f"❌ PROMPTS_PROFILE={prof} (ожидаем 'v2')")
            ok = False

        if ok:
            self.stdout.write(self.style.SUCCESS("✅ preflight_v2_prod: всё ок, легаси не найдено."))
        else:
            raise SystemExit(1)