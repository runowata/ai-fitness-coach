import json, pathlib, re, sys

# Все *.json где-нибудь внутри каталога fixtures
root = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

INT_IS_ID = re.compile(r"(^pk$|_id$|_ids$|^parent$|^exercise$|^achievement$)", re.I)

def cast(value):
    if isinstance(value, int):
        return str(value)        # 42 -> "42"
    if isinstance(value, list):
        return [cast(x) for x in value]
    if isinstance(value, dict):
        return {k: cast(v) for k, v in value.items()}
    return value

def patch(obj):
    # pk
    if isinstance(obj.get("pk"), int):
        obj["pk"] = str(obj["pk"])
    # fields
    f = obj.get("fields", {})
    for k, v in list(f.items()):
        if INT_IS_ID.search(k):
            f[k] = cast(v)

for path in root.rglob("*.json"):          #  ← рекурсивно!
    data = json.load(open(path))
    changed = False
    for o in data:
        before = json.dumps(o, sort_keys=True)
        patch(o)
        if json.dumps(o, sort_keys=True) != before:
            changed = True
    if changed:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)
        print(f"✔  Patched {path.relative_to(root.parent)}")
    else:
        print(f"•  {path.relative_to(root.parent)} unchanged")
print("🏁  Done.")