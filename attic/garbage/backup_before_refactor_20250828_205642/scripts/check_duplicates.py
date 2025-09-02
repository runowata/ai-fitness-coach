from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")

# Проверяем базу упражнений
print("🔍 Checking base_exercises.xlsx...")
df_ex = pd.read_excel(RAW_DIR / "base_exercises.xlsx")
print(f"   Total rows: {len(df_ex)}")
dups = len(df_ex) - len(df_ex.drop_duplicates())
if dups > 0:
    print(f"   ⚠️  Found {dups} duplicate rows")
    df_ex = df_ex.drop_duplicates()
    df_ex.to_excel(RAW_DIR / "base_exercises.xlsx", index=False)
    print(f"   ✅ Cleaned! New total: {len(df_ex)}")
else:
    print("   ✅ No duplicates found")

# Проверяем файлы с видео
for video_file in ["explainer_videos_111_nastavnik.xlsx", 
                   "explainer_videos_222_professional.xlsx", 
                   "explainer_videos_333_rovesnik.xlsx"]:
    if (RAW_DIR / video_file).exists():
        print(f"\n🔍 Checking {video_file}...")
        df = pd.read_excel(RAW_DIR / video_file)
        print(f"   Total rows: {len(df)}")
        dups = len(df) - len(df.drop_duplicates())
        if dups > 0:
            print(f"   ⚠️  Found {dups} duplicate rows")
            df = df.drop_duplicates()
            df.to_excel(RAW_DIR / video_file, index=False)
            print(f"   ✅ Cleaned! New total: {len(df)}")
        else:
            print("   ✅ No duplicates found")