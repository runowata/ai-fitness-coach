import json, pathlib, sys, re
root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

# Собираем все pk (как строки)
ids_seen = set()
for p in root.rglob("*.json"):
    for o in json.load(open(p)):
        pk = o.get("pk")
        if isinstance(pk, int):
            ids_seen.add(str(pk))
        elif isinstance(pk, str) and pk.isdigit():
            ids_seen.add(pk)

def stringify(v):
    if isinstance(v, int) and str(v) in ids_seen:
        return str(v)
    if isinstance(v, list):
        return [stringify(x) for x in v]
    if isinstance(v, dict):
        return {k: stringify(x) for k, x in v.items()}
    return v

for path in root.rglob("*.json"):
    data = json.load(open(path))
    changed = False
    for o in data:
        if isinstance(o["pk"], int):
            o["pk"] = str(o["pk"]); changed = True
        new_fields = stringify(o.get("fields", {}))
        if new_fields != o.get("fields", {}):
            o["fields"] = new_fields; changed = True
    if changed:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)
        print("✔", path.relative_to(root.parent))
    else:
        print("•", path.relative_to(root.parent), "untouched")
print("🏁 done")