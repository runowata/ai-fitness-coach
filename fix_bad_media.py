#!/usr/bin/env python3
# fix_bad_media.py
"""
 Убирает дубли, переименовывает «криво» названные видео
 и удаляет битые файлы в selected_media.
"""

import hashlib
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT   = Path(__file__).resolve().parent
MEDIA  = ROOT / "selected_media"
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

MIN_VIDEO_BYTES = 200 * 1024      # 200 КБ
MIN_PHOTO_BYTES = 5 * 1024        # 5 КБ

TARGET_REGEX = {
    "videos/exercises/explain": re.compile(r".+_explain_m01\.[\w\d]+$"),
    "videos/reminders":         re.compile(r"reminder_\d{3}\.[\w\d]+$"),
    "videos/intros":            re.compile(r"intro_\d{2}\.[\w\d]+$"),
    "videos/weekly":            re.compile(r"weekly_\d{2}\.[\w\d]+$"),
    "videos/closing":           re.compile(r"closing_\d{2}\.[\w\d]+$"),
}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def duration_ok(p: Path) -> bool:
    if p.suffix.lower() not in VIDEO_EXTS: return True
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", str(p)],
            text=True, timeout=15)
        dur = float(out.strip())
        return dur > 0
    except Exception:
        return False

def next_number(dir_: Path, prefix: str, width: int) -> int:
    nums = [int(m.group()) for f in dir_.glob(f"{prefix}*")
            if (m := re.search(r"(\d+)", f.stem))]
    return (max(nums)+1) if nums else 1

def main() -> None:
    duplicate_counter = 0
    rename_counter    = 0
    removed_counter   = 0
    
    # First pass: collect all hashes and identify duplicates
    all_files = {}  # hash -> [list of files]
    
    for cat, regex in TARGET_REGEX.items():
        folder = MEDIA / cat
        if not folder.exists(): continue

        for f in sorted(folder.iterdir()):
            if not f.is_file(): continue
            
            # Skip corrupt videos first
            if not duration_ok(f):
                f.unlink()
                removed_counter += 1
                print(f"🗑️  removed corrupt {f.relative_to(MEDIA)}")
                continue
            
            # Check for empty or tiny files
            size = f.stat().st_size
            if size == 0:
                f.unlink()
                removed_counter += 1
                print(f"🗑️  removed empty {f.relative_to(MEDIA)}")
                continue
            elif f.suffix.lower() in VIDEO_EXTS and size < MIN_VIDEO_BYTES:
                f.unlink()
                removed_counter += 1
                print(f"🗑️  removed tiny video {f.relative_to(MEDIA)} ({size//1024} KB)")
                continue
            elif f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.webp'} and size < MIN_PHOTO_BYTES:
                f.unlink()
                removed_counter += 1
                print(f"🗑️  removed tiny photo {f.relative_to(MEDIA)} ({size//1024} KB)")
                continue
                
            h = sha256(f)
            if h not in all_files:
                all_files[h] = []
            all_files[h].append(f)
    
    # Second pass: remove duplicates
    for h, files in all_files.items():
        if len(files) > 1:
            # Keep oldest file, remove others
            oldest = min(files, key=lambda p: p.stat().st_mtime)
            for dup in files:
                if dup != oldest:
                    dup.unlink()
                    duplicate_counter += 1
                    print(f"🗑️  removed duplicate {dup.relative_to(MEDIA)}")
    
    # Third pass: rename files that don't match regex
    for cat, regex in TARGET_REGEX.items():
        folder = MEDIA / cat
        if not folder.exists(): continue

        for f in sorted(folder.iterdir()):
            if not f.is_file(): continue

            if not regex.match(f.name):
                prefix, width = {
                    "videos/exercises/explain": ("ex",     3),
                    "videos/reminders":         ("reminder_",3),
                    "videos/weekly":            ("weekly_", 2),
                    "videos/intros":            ("intro_",  2),
                    "videos/closing":           ("closing_",2),
                }[cat]
                num = next_number(folder, prefix, width)
                new_name = {
                    "videos/exercises/explain": f"{f.stem[:20]}_explain_m01{f.suffix.lower()}",
                    "videos/reminders":         f"reminder_{num:03d}{f.suffix.lower()}",
                    "videos/weekly":            f"weekly_{num:02d}{f.suffix.lower()}",
                    "videos/intros":            f"intro_{num:02d}{f.suffix.lower()}",
                    "videos/closing":           f"closing_{num:02d}{f.suffix.lower()}",
                }[cat]
                f.rename(folder / new_name)
                rename_counter += 1
                print(f"✏️  rename {f.name} → {new_name}")

    print("\n✅ Done:",
          f"{rename_counter} renamed,",
          f"{duplicate_counter} duplicates removed,",
          f"{removed_counter} corrupt removed")

if __name__ == "__main__":
    main()