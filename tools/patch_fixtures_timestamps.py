#!/usr/bin/env python3
# tools/patch_fixtures_timestamps.py
import os, json, glob, pathlib, re, sys
from datetime import datetime, timezone

# ---- Django bootstrap ----
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.apps import apps
from django.db.models import DateTimeField

FIXTURES_GLOB = os.environ.get("FIXTURES_GLOB", "fixtures/*.json")
STAMP = os.environ.get("TZ_STAMP", "2025-08-01T00:36:20+00:00")

def is_tz_aware_iso(s: str) -> bool:
    return isinstance(s, str) and re.search(r"(Z|[+-]\d{2}:\d{2})$", s) is not None

def to_tz_aware(s):
    if s is None:
        return STAMP
    if isinstance(s, str) and s.strip() == "":
        return STAMP
    if isinstance(s, str) and not is_tz_aware_iso(s):
        return s + "+00:00"
    return s

# Which field names to force if present & required
TARGET_FIELD_NAMES = {"created_at", "updated_at"}

def model_datetime_requirements(model):
    """Return set of required datetime field names for model (null=False)."""
    required = set()
    for f in model._meta.get_fields():
        if isinstance(getattr(f, "target_field", f), DateTimeField):
            # Skip reverse/relation fields
            if not hasattr(f, "null"): 
                continue
            if f.name in TARGET_FIELD_NAMES and (getattr(f, "null", True) is False):
                required.add(f.name)
    return required

def patch_file(path: pathlib.Path) -> int:
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"⚠️  Skip (not JSON): {path} ({e})")
        return 0
    if not isinstance(data, list):
        print(f"⚠️  Skip (not a list): {path}")
        return 0

    changed = 0
    for obj in data:
        app_model = obj.get("model")
        fields = obj.setdefault("fields", {})
        if not app_model:
            continue
        try:
            app_label, model_name = app_model.split(".", 1)
        except ValueError:
            continue
        try:
            model = apps.get_model(app_label, model_name, require_ready=False)
        except LookupError:
            continue
        if model is None:
            continue

        required = model_datetime_requirements(model)
        if not required:
            continue

        touched_this_obj = False
        for fname in sorted(required):
            cur = fields.get(fname)
            newv = to_tz_aware(cur)
            if newv != cur:
                fields[fname] = newv
                touched_this_obj = True
        if touched_this_obj:
            changed += 1

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✓ {path}: patched {changed} object(s)")
    else:
        print(f"• {path}: no changes")
    return changed

def main():
    total = 0
    for fp in sorted(glob.glob(FIXTURES_GLOB)):
        total += patch_file(pathlib.Path(fp))
    if total == 0:
        print("Nothing patched.")
    else:
        print(f"Done. Total objects patched: {total}")

if __name__ == "__main__":
    main()