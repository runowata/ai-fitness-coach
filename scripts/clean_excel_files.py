import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")

print("🧹 Cleaning Excel files...")

# 1. Очистка base_exercises.xlsx
print("\n📋 Cleaning base_exercises.xlsx...")
df = pd.read_excel(RAW_DIR / "base_exercises.xlsx", header=1)

# Удаляем строки где ID = "ID" (дублированные заголовки)
df = df[df['ID'] != 'ID']

# Удаляем строки где ID = "---" (разделители)
df = df[~df['ID'].str.contains('---', na=False)]

# Удаляем строки с пустым ID
df = df.dropna(subset=['ID'])

# Исправляем дублирующиеся ID
# Находим все дубликаты
duplicated_ids = df[df.duplicated(subset='ID', keep=False)].copy()
if len(duplicated_ids) > 0:
    print(f"   Found {len(duplicated_ids)} rows with duplicate IDs")
    
    # Группируем по ID и добавляем суффикс
    for idx, (ex_id, group) in enumerate(duplicated_ids.groupby('ID')):
        if len(group) > 1:
            print(f"   Fixing ID {ex_id} ({len(group)} duplicates)")
            # Первое вхождение оставляем как есть
            # К остальным добавляем суффикс _v2, _v3 и т.д.
            counter = 2
            for row_idx in group.index[1:]:  # Пропускаем первое
                new_id = f"{ex_id}_v{counter}"
                df.loc[row_idx, 'ID'] = new_id
                print(f"     {ex_id} -> {new_id}: {df.loc[row_idx, 'Название (RU)']}")
                counter += 1

# Сохраняем очищенный файл
df.to_excel(RAW_DIR / "base_exercises_clean.xlsx", index=False)
print(f"   ✅ Saved {len(df)} clean exercises to base_exercises_clean.xlsx")

# 2. Переименовываем очищенный файл
(RAW_DIR / "base_exercises.xlsx").rename(RAW_DIR / "base_exercises_original.xlsx")
(RAW_DIR / "base_exercises_clean.xlsx").rename(RAW_DIR / "base_exercises.xlsx")
print("   ✅ Replaced original file (backup saved as base_exercises_original.xlsx)")

# 3. Очистка файлов с видео (на случай если там тоже есть мусор)
for video_file in ["explainer_videos_111_nastavnik.xlsx", 
                   "explainer_videos_222_professional.xlsx", 
                   "explainer_videos_333_rovesnik.xlsx"]:
    if (RAW_DIR / video_file).exists():
        print(f"\n📹 Checking {video_file}...")
        df_vid = pd.read_excel(RAW_DIR / video_file)
        initial_len = len(df_vid)
        
        # Проверяем какая колонка с ID упражнения
        id_col = None
        for col in ['exercise_id', 'Exercise ID', 'ID']:
            if col in df_vid.columns:
                id_col = col
                break
        
        if id_col:
            # Удаляем строки с пустым ID
            df_vid = df_vid.dropna(subset=[id_col])
            
            # Удаляем строки где ID начинается с ---
            df_vid = df_vid[~df_vid[id_col].astype(str).str.contains('---', na=False)]
        
        if len(df_vid) < initial_len:
            df_vid.to_excel(RAW_DIR / video_file, index=False)
            print(f"   ✅ Cleaned: {initial_len} -> {len(df_vid)} rows")
        else:
            print(f"   ✅ Already clean: {len(df_vid)} rows")

print("\n✅ All files cleaned!")