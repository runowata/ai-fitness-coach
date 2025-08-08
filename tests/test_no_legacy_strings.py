"""
Test to ensure no legacy strings remain in codebase
"""
import pathlib
import re

BAD = re.compile(r"(prompts/v1|DEFAULT_FILE_STORAGE|S3_ADDRESSING_STYLE|FileSystemStorage|MEDIA_ROOT\b|bro\b|sergeant\b|intellectual\b)")
EXCLUDE = ("migrations/", "docs/", "R2_MEDIA_DOCUMENTATION.md", "CHANGELOG.md", "fill_placeholders.py", "media_organizer/", "r2_upload_state.json")

def test_no_legacy_strings():
    """Test that legacy archetype strings are not present in code"""
    root = pathlib.Path(__file__).resolve().parents[1]
    offenders = []
    
    for p in root.rglob("*.*"):
        s = str(p)
        if any(x in s for x in EXCLUDE):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if BAD.search(txt):
            offenders.append(s)
    
    assert not offenders, f"Legacy mentions found:\n" + "\n".join(offenders[:50])

def test_new_archetypes_present():
    """Test that new archetype strings are used"""
    root = pathlib.Path(__file__).resolve().parents[1]
    
    # Check for new archetypes in key files
    models_file = root / "apps" / "workouts" / "models.py"
    if models_file.exists():
        content = models_file.read_text()
        assert "peer" in content, "New archetype 'peer' not found in models"
        assert "professional" in content, "New archetype 'professional' not found in models"
        assert "mentor" in content, "New archetype 'mentor' not found in models"