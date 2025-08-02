import pandas as pd
from slugify import slugify
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 1. Exercises ----------
# Читаем файл (теперь заголовки на первой строке)
df_ex = pd.read_excel(RAW_DIR / "base_exercises.xlsx")

# Приводим имена колонок в snake_case латиницей
df_ex.columns = [slugify(str(c), separator="_") for c in df_ex.columns]

# Показываем какие колонки нашли
print(f"Found columns in base_exercises.xlsx: {list(df_ex.columns)}")

# Переименовываем колонки в стандартные имена
rename_map = {
    "id": "id",
    "nazvanie_ru": "name_ru",
    "nazvanie_en": "name_en", 
    "slozhnost": "level",
    "kratkoe_opisanie": "description",
    "osnovnaya_myshechnaya_gruppa": "muscle_group",
    "tip_uprazhneniya": "exercise_type",
    "klyuchevye_tegi_dlya_ii": "ai_tags"
}
df_ex = df_ex.rename(columns=rename_map)

# Обязательные поля
required = {"id", "name_ru", "name_en", "level"}
missing = required - set(df_ex.columns)
if missing:
    print(f"Missing required columns: {missing}")
    print(f"Available columns: {list(df_ex.columns)}")
    raise ValueError(f"Missing columns in base_exercises.xlsx: {missing}")

# Удаляем дубли id
dups = df_ex[df_ex.duplicated(subset="id", keep=False)]
if len(dups):
    print("⚠️  DUPLICATE IDs in base_exercises.xlsx:")
    print(dups[["id", "name_ru"]])
df_ex = df_ex.drop_duplicates(subset="id", keep="first")

df_ex.to_csv(OUT_DIR / "exercises.csv", index=False)
print(f"✅ Saved {len(df_ex)} exercises")

# ---------- 2. Explainer videos ----------
# Ищем все файлы с видео-объяснениями
video_files = list(RAW_DIR.glob("*explainer*.xlsx")) + \
              list(RAW_DIR.glob("*video*.xlsx")) + \
              list(RAW_DIR.glob("*ролик*.xlsx"))

if not video_files:
    print("⚠️  No explainer video files found!")
    print(f"   Looking in: {RAW_DIR}")
    print(f"   Files there: {list(RAW_DIR.glob('*.xlsx'))}")
else:
    all_videos = []
    
    for vf in video_files:
        print(f"\n📄 Processing: {vf.name}")
        
        df_vid = pd.read_excel(vf)
        df_vid.columns = [slugify(c, separator="_") for c in df_vid.columns]
        
        # Добавляем архетип из имени файла, если его нет
        if "archetype" not in df_vid.columns:
            # Пытаемся извлечь архетип из имени файла по коду
            fname = vf.stem
            if "111" in fname:
                df_vid["archetype"] = "nastavnik"
                df_vid["archetype_code"] = "111"
            elif "222" in fname:
                df_vid["archetype"] = "professional"
                df_vid["archetype_code"] = "222"
            elif "333" in fname:
                df_vid["archetype"] = "rovesnik"
                df_vid["archetype_code"] = "333"
            else:
                print(f"   ⚠️  Cannot detect archetype code (111/222/333) from filename: {vf.name}")
        
        # Приводим к единому ключу exercise_id
        if "exercise_id" not in df_vid.columns:
            # Пытаемся угадать альтернативные имена
            for alt in ["id_ex", "ex_id", "exerciseid", "id", "exercise"]:
                if alt in df_vid.columns:
                    df_vid = df_vid.rename(columns={alt: "exercise_id"})
                    break
        
        required_v = {"exercise_id", "video_path"}
        missing_v = required_v - set(df_vid.columns)
        if missing_v:
            print(f"   ⚠️  Missing columns: {missing_v}")
            print(f"   Available columns: {list(df_vid.columns)}")
            continue
        
        # Проверяем, есть ли видео для несуществующих упражнений
        orphans = df_vid[~df_vid["exercise_id"].isin(df_ex["id"])]
        if len(orphans):
            print(f"   ⚠️  {len(orphans)} videos without matching exercise")
        
        print(f"   ✅ Found {len(df_vid)} videos")
        all_videos.append(df_vid)
    
    if all_videos:
        # Объединяем все видео
        df_all_videos = pd.concat(all_videos, ignore_index=True)
        df_all_videos.to_csv(OUT_DIR / "explainer_videos.csv", index=False)
        print(f"\n✅ Saved total {len(df_all_videos)} explainer videos")