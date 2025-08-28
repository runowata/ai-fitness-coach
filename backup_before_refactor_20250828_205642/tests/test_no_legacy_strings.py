"""
Test to ensure no legacy strings remain in codebase
"""
import pathlib
import re

BAD = re.compile(r"(prompts/v1|DEFAULT_FILE_STORAGE|S3_ADDRESSING_STYLE|FileSystemStorage|MEDIA_ROOT\b|(?<![A-Za-z])(bro|sergeant|intellectual)(?![A-Za-z]))")
ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "migrations", "docs", "media_organizer", "staticfiles", "__pycache__"}
EXTS = {".py", ".html", ".js", ".ts", ".tsx", ".css"}

def test_no_legacy_strings():
    """Test that legacy archetype strings are not present in code"""
    offenders = []
    for p in ROOT.rglob("*"):
        if p.is_dir():
            if p.name in SKIP_DIRS:
                # Skip entire subdirectories
                continue
        if not p.is_file() or p.suffix not in EXTS:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if BAD.search(txt):
            offenders.append(str(p))
    
    assert not offenders, "Legacy mentions found:\n" + "\n".join(offenders[:100])

def test_new_archetypes_present():
    """Test that new archetype strings are used"""
    # Check for new archetypes in key files
    models_file = ROOT / "apps" / "workouts" / "models.py"
    if models_file.exists():
        content = models_file.read_text()
        assert "peer" in content, "New archetype 'peer' not found in models"
        assert "professional" in content, "New archetype 'professional' not found in models"
        assert "mentor" in content, "New archetype 'mentor' not found in models"