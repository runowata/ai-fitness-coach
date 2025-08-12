"""
Создание маппинга между Excel ID и R2 названиями упражнений
"""
import pandas as pd
import json
import re

def normalize_name(name):
    """Нормализация названий для сопоставления"""
    name = str(name).lower()
    # Убираем скобки и содержимое
    name = re.sub(r'\([^)]*\)', '', name)
    # Убираем спецсимволы
    name = re.sub(r'[^\w\s-]', '', name)
    # Заменяем пробелы на дефисы
    name = re.sub(r'\s+', '-', name.strip())
    # Убираем множественные дефисы
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

def create_excel_r2_mapping():
    """Создает маппинг между Excel ID и R2 названиями"""
    
    # Загрузка данных
    df = pd.read_excel('./data/raw/base_exercises.xlsx')
    with open('r2_upload_state.json', 'r') as f:
        r2_data = json.load(f)

    # Получаем все коды упражнений из R2
    r2_exercise_codes = set()
    for filepath in r2_data:
        if 'videos/exercises/' in filepath:
            filename = filepath.split('/')[-1]
            if '_technique_' in filename or '_mistake_' in filename:
                exercise_code = filename.split('_')[0]
                r2_exercise_codes.add(exercise_code)

    mapping = {}
    unmatched_r2 = list(r2_exercise_codes)

    for i, row in df.iterrows():
        excel_id = row['ID']
        name_en = row['Название (EN)']
        
        normalized = normalize_name(name_en)
        
        # Прямое сопоставление
        if normalized in r2_exercise_codes:
            mapping[excel_id] = normalized
            if normalized in unmatched_r2:
                unmatched_r2.remove(normalized)
            continue
        
        # Частичное сопоставление
        found = False
        for r2_code in r2_exercise_codes:
            # Проверяем, содержится ли нормализованное название в R2 коде
            if normalized in r2_code or r2_code in normalized:
                mapping[excel_id] = r2_code
                if r2_code in unmatched_r2:
                    unmatched_r2.remove(r2_code)
                found = True
                break
            
            # Проверяем по ключевым словам
            excel_words = set(normalized.split('-'))
            r2_words = set(r2_code.split('-'))
            
            # Если есть значительное пересечение слов
            if len(excel_words & r2_words) >= 2:
                mapping[excel_id] = r2_code
                if r2_code in unmatched_r2:
                    unmatched_r2.remove(r2_code)
                found = True
                break

    print(f"Создано сопоставлений: {len(mapping)} из {len(df)}")
    print(f"Не сопоставлено из R2: {len(unmatched_r2)}")
    
    return mapping

if __name__ == "__main__":
    mapping = create_excel_r2_mapping()
    with open('excel_r2_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    print("Маппинг сохранен в excel_r2_mapping.json")