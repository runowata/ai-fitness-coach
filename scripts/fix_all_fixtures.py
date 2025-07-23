import json, pathlib

root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

# Define which fields each model should have
MODEL_TIMESTAMP_FIELDS = {
    "workouts.exercise": ["created_at", "updated_at"],
    "achievements.achievement": ["created_at"],
    "content.story": ["created_at", "updated_at"],  # Story has updated_at!
    "content.storychapter": ["created_at"],
    "workouts.videoclip": ["created_at"],
    "onboarding.onboardingquestion": ["created_at", "updated_at"],
    "onboarding.motivationalcard": ["created_at"],
    "onboarding.answeroption": []  # No timestamp fields
}

for path in root.glob("*.json"):
    changed = False
    data = json.load(open(path))
    
    for obj in data:
        model = obj.get("model")
        if model in MODEL_TIMESTAMP_FIELDS:
            fields = obj.get("fields", {})
            allowed_timestamps = MODEL_TIMESTAMP_FIELDS[model]
            
            # Remove timestamp fields that shouldn't be there
            for field in ["created_at", "updated_at"]:
                if field in fields and field not in allowed_timestamps:
                    del fields[field]
                    changed = True
            
            # Add missing timestamp fields that should be there
            for field in allowed_timestamps:
                if field not in fields:
                    fields[field] = "2025-07-23T00:00:00Z"
                    changed = True
    
    if changed:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)
        print(f"✔ Fixed {path.name}")
    else:
        print(f"• {path.name} already correct")