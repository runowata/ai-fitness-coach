#!/usr/bin/env python3
# validate_media.py
"""
Проверяет, что selected_media соответствует всем требованиям:
  • точные количества файлов по категориям
  • нет дублей (SHA-256)
  • все видео ≤ 7 мин и ≤ 600 МБ
  • общий объём добавленных файлов ≤ 10 ГБ (смотрим media_fill_log.csv)
  • имена файлов соответствуют шаблонам
Выводит цветной отчёт; при ошибках завершается exit-кодом 1.
"""

import csv
import hashlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich import print
from rich.table import Table

ROOT   = Path(__file__).resolve().parent
MEDIA  = ROOT / "selected_media"
LOG    = ROOT / "media_fill_log.csv"

MIN_VIDEO_BYTES = 200 * 1024      # 200 КБ
MIN_PHOTO_BYTES = 5 * 1024        # 5 КБ
tiny_or_empty = []                # (Path, reason) куда будем складывать

TARGET = {
    "videos/exercises/explain": 147,
    "videos/reminders":         441,
    "videos/intros":             15,
    "videos/weekly":              5,
    "videos/closing":            10,
    "photos/quotes":           1000,
    "photos/workout":           500,
    "photos/progress":          500,
}

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_SEC, MAX_MB, MAX_TOTAL_MB = 7*60, 600, 10*1024

regex_name = {
    "videos/exercises/explain": re.compile(r".+_explain_m01\.[\w\d]+$"),
    "videos/reminders":         re.compile(r"reminder_\d{3}\.[\w\d]+$"),
    "videos/intros":            re.compile(r"intro_\d{2}\.[\w\d]+$"),
    "videos/weekly":            re.compile(r"weekly_\d{2}\.[\w\d]+$"),
    "videos/closing":           re.compile(r"closing_\d{2}\.[\w\d]+$"),
    "photos/quotes":            re.compile(r"card_quotes_\d{4}\.jpg$"),
    "photos/workout":           re.compile(r"card_workout_\d{4}\.jpg$"),
    "photos/progress":          re.compile(r"card_progress_\d{4}\.jpg$"),
}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def duration_sec(p: Path) -> float:
    if p.suffix.lower() not in VIDEO_EXTS: return 0
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", str(p)],
            text=True, timeout=15)
        return float(out.strip())
    except Exception:
        return 0

def load_log_size_mb() -> float:
    if not LOG.exists(): return 0
    with LOG.open() as f:
        reader = csv.DictReader(f)
        return sum(float(r["size_MB"]) for r in reader if r["action"]=="add")

def main() -> int:
    errors = []
    table  = Table(title="Media validation results", show_lines=True)
    table.add_column("Category"); table.add_column("Have/Target")
    table.add_column("Missing");  table.add_column("Issues")

    total_added_mb = load_log_size_mb()

    seen_hashes = set()
    for cat, target in TARGET.items():
        path = MEDIA / cat
        files = [f for f in path.glob("*") if f.is_file()]
        have  = len(files)
        miss  = max(0, target - have)
        issue = []

        # количество
        if miss != 0:
            issue.append(f"[red]count[/red]")

        # имя + ограничения + дубликаты + размер
        for f in files:
            if not regex_name[cat].match(f.name):
                issue.append("name")
            h = sha256(f)
            if h in seen_hashes:
                issue.append("duplicate")
            seen_hashes.add(h)
            
            # Проверка размера файла
            size = f.stat().st_size
            if size == 0:
                tiny_or_empty.append((f, "empty (0 B)"))
                issue.append("empty")
            elif f.suffix.lower() in {'.mp4', '.mov', '.avi', '.mkv', '.webm'} and size < MIN_VIDEO_BYTES:
                tiny_or_empty.append((f, f"too small ({size//1024} KB)"))
                issue.append("tiny")
            elif f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.webp'} and size < MIN_PHOTO_BYTES:
                tiny_or_empty.append((f, f"too small ({size//1024} KB)"))
                issue.append("tiny")
            
            if f.suffix.lower() in VIDEO_EXTS:
                if f.stat().st_size > MAX_MB*1024**2:
                    issue.append("size")
                if duration_sec(f) > MAX_SEC:
                    issue.append("duration")

        issue_txt = ", ".join(sorted(set(issue))) or "[green]OK[/green]"
        if "red" in issue_txt or miss>0: errors.append(cat)
        table.add_row(cat, f"{have}/{target}", str(miss), issue_txt)

    print(table)
    # проверка суммарного добавленного объёма
    if total_added_mb > MAX_TOTAL_MB:
        print(f"[red]❌ В логе добавлено {total_added_mb:.1f} МБ (> 10 ГБ)[/red]")
        errors.append("total_size")
    else:
        print(f"[green]✓ Добавленный объём по логу: {total_added_mb:.1f} МБ[/green]")

    if tiny_or_empty:
        print("\n❌  Suspiciously small / empty files:")
        for p, why in tiny_or_empty:
            print(f"   • {p.relative_to(MEDIA)} – {why}")
        errors.append("tiny_or_empty")

    if errors:
        print(f"[red]Найдены проблемы в категориях: {', '.join(errors)}[/red]")
        return 1
    print("[bold green]Все проверки пройдены![/bold green]")
    return 0

if __name__ == "__main__":
    sys.exit(main())