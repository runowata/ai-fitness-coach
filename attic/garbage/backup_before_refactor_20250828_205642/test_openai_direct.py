#!/usr/bin/env python
"""
Прямой тест OpenAI API без Django
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем API ключ
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else ''}")

# Проверяем, что ключ валидный
if not api_key or not api_key.startswith('sk-'):
    print("❌ Невалидный API ключ!")
    print("Пожалуйста, вставьте полный API ключ в файл .env")
    exit(1)

# Проверяем наличие русских символов
try:
    api_key.encode('ascii')
    print("✅ Ключ не содержит нелатинских символов")
except UnicodeEncodeError:
    print("❌ Ключ содержит нелатинские символы!")
    print("Замените русские буквы на полный API ключ")
    exit(1)

print("\nПытаемся подключиться к OpenAI API...")

try:
    from openai import OpenAI
    
    # Создаем клиент
    client = OpenAI(api_key=api_key)
    
    # Пробуем простой запрос к GPT-3.5 (он точно существует)
    print("Тестируем с моделью gpt-3.5-turbo...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API works!'"}],
        max_tokens=10
    )
    
    print(f"✅ GPT-3.5 работает: {response.choices[0].message.content}")
    
    # Теперь пробуем GPT-4
    print("\nТестируем с моделью gpt-4...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'GPT-4 works!'"}],
            max_tokens=10
        )
        print(f"✅ GPT-4 работает: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ GPT-4 ошибка: {e}")
    
    # Теперь пробуем GPT-5 с новым Responses API
    print("\nТестируем с моделью gpt-5 (Responses API)...")
    try:
        response = client.responses.create(
            model="gpt-5",
            input="Say 'GPT-5 works!'",
            text={"verbosity": "low"}
        )
        
        # Извлекаем текст из ответа
        output_text = ""
        for item in response.output:
            if hasattr(item, "content"):
                for content in item.content:
                    if hasattr(content, "text"):
                        output_text += content.text
        
        print(f"✅ GPT-5 работает: {output_text}")
        
    except AttributeError as e:
        print(f"❌ GPT-5 ошибка: Responses API не найден. Возможно, нужно обновить OpenAI SDK")
        print(f"   Детали: {e}")
    except Exception as e:
        print(f"❌ GPT-5 ошибка: {e}")
        
        # Если ошибка 404, значит модель не существует
        if "404" in str(e) or "model" in str(e).lower():
            print("   Модель gpt-5 не найдена. Возможно, у вас нет доступа к GPT-5")
            print("   или модель еще не выпущена публично")
    
except Exception as e:
    print(f"❌ Ошибка подключения к OpenAI: {e}")
    print("\nВозможные причины:")
    print("1. Неверный API ключ")
    print("2. Нет интернет-соединения")
    print("3. API ключ не имеет нужных прав доступа")