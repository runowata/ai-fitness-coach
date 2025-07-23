import json, pathlib
from datetime import datetime

root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

# Fields that need timestamps
TIMESTAMP_FIELDS = ["created_at", "updated_at"]

for path in root.glob("*.json"):
    changed = False
    data = json.load(open(path))
    
    for obj in data:
        fields = obj.get("fields", {})
        
        # Add missing timestamp fields
        for field in TIMESTAMP_FIELDS:
            if field not in fields and "created_at" in fields:
                # If created_at exists but updated_at doesn't, copy created_at
                fields["updated_at"] = fields["created_at"]
                changed = True
            elif field not in fields:
                # Add default timestamp
                fields[field] = "2025-07-23T00:00:00Z"
                changed = True
    
    if changed:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)
        print(f"✔ Added timestamps to {path.name}")
    else:
        print(f"• {path.name} already has timestamps")