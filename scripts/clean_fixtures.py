import json, pathlib

root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

# Models that don't have updated_at field
MODELS_WITHOUT_UPDATED_AT = [
    "achievements.achievement",
    "content.story", 
    "content.storychapter",
    "workouts.videoclip",
    "onboarding.motivationalcard"  # Removed onboardingquestion as it has updated_at
]

for path in root.glob("*.json"):
    changed = False
    data = json.load(open(path))
    
    for obj in data:
        if obj.get("model") in MODELS_WITHOUT_UPDATED_AT:
            fields = obj.get("fields", {})
            if "updated_at" in fields:
                del fields["updated_at"]
                changed = True
    
    if changed:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)
        print(f"✔ Cleaned {path.name}")
    else:
        print(f"• {path.name} already clean")