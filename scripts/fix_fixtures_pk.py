import json, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
for path in root.glob("*.json"):
    data = json.load(open(path))
    changed = False
    for obj in data:
        if isinstance(obj.get("pk"), int):
            obj["pk"] = str(obj["pk"])
            changed = True
    if changed:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)
        print(f"✔ Patched {path.name}")
    else:
        print(f"• {path.name} unchanged (already strings)")