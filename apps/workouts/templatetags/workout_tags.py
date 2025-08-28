"""Template tags for workout-related functionality"""

from django import template

register = template.Library()


@register.filter
def extract_r2_key(file_url):
    """
    Извлекает ключ из R2 URL для использования в media_proxy
    
    Examples:
        r2://videos/exercises/push_up_technique.mp4 -> videos/exercises/push_up_technique.mp4
        /videos/exercises/push_up_technique.mp4 -> videos/exercises/push_up_technique.mp4
        videos/exercises/push_up_technique.mp4 -> videos/exercises/push_up_technique.mp4
    """
    if not file_url:
        return ""
    
    # Убираем префикс r2:// если есть
    if file_url.startswith("r2://"):
        return file_url[5:]  # Убираем "r2://"
    
    # Убираем ведущий слеш если есть
    if file_url.startswith("/"):
        return file_url[1:]  # Убираем "/"
    
    # Возвращаем как есть
    return file_url


@register.filter 
def exercise_count_plural(count):
    """
    Склонение слова "упражнение" в зависимости от количества
    
    Examples:
        1 -> "упражнение"
        2-4 -> "упражнения" 
        5+ -> "упражнений"
    """
    if count == 1:
        return "упражнение"
    elif 2 <= count <= 4:
        return "упражнения"
    else:
        return "упражнений"