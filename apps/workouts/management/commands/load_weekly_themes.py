from django.core.management.base import BaseCommand
from apps.workouts.models import WeeklyTheme


class Command(BaseCommand):
    help = 'Load weekly themes for structured course progression'

    def handle(self, *args, **options):
        # Based on reference documents analysis - 8-week course structure
        weekly_themes = [
            {
                'week_number': 1,
                'theme_title': 'Фундамент удовольствия: дыхание и мышцы тазового дна',
                'focus_area': 'Дыхание и основы тела',
                'description': 'Знакомство с основами дыхания и понимание работы мышц тазового дна',
                'mentor_content': 'Начнем с самого важного - умения слышать свое тело и дышать осознанно. Это фундамент всего пути.',
                'professional_content': 'Неделя 1 - базовая настройка системы. Изучаем анатомию и физиологию для максимального КПД.',
                'peer_content': 'Привет! Начинаем наше путешествие. На этой неделе учимся чувствовать свое тело и правильно дышать.',
            },
            {
                'week_number': 2,
                'theme_title': 'Техника #1 - Карта вашего тела',
                'focus_area': 'Изучение тела и первые техники',
                'description': 'Создание внутренней карты чувствительности и изучение техник стимуляции',
                'mentor_content': 'Сегодня мы начинаем исследование - создаем карту ваших ощущений с терпением и любопытством.',
                'professional_content': 'Неделя 2 - картирование эрогенных зон. Системный подход к изучению точек стимуляции.',
                'peer_content': 'Время узнать свое тело лучше! Будем исследовать и создавать карту того, что нам нравится.',
            },
            {
                'week_number': 3,
                'theme_title': 'Психология желания: спонтанное vs реактивное либидо',
                'focus_area': 'Понимание психологии сексуальности',
                'description': 'Изучение различных типов либидо и работа с психологическими аспектами',
                'mentor_content': 'Понимание природы желания - ключ к гармонии с собой. Примем все формы либидо с мудростью.',
                'professional_content': 'Неделя 3 - анализ психосексуальных паттернов. Оптимизация либидо под ваш тип.',
                'peer_content': 'Разбираемся с тем, как работает наше желание. Это нормально, если оно у всех разное!',
            },
            {
                'week_number': 4,
                'theme_title': 'Техника #2 - Управление энергией (Edging)',
                'focus_area': 'Продвинутые техники контроля',
                'description': 'Изучение техник эджинга и управления сексуальной энергией',
                'mentor_content': 'Искусство управления энергией требует терпения. Мы учимся не торопиться и наслаждаться процессом.',
                'professional_content': 'Неделя 4 - протоколы эджинга для максимизации удовольствия и контроля.',
                'peer_content': 'Изучаем крутую технику! Эджинг поможет нам стать мастерами своего удовольствия.',
            },
            {
                'week_number': 5,
                'theme_title': 'Сексуальная коммуникация: boundaries и consent',
                'focus_area': 'Коммуникация и границы',
                'description': 'Навыки общения о сексе, установление границ и согласие',
                'mentor_content': 'Честная коммуникация - основа близости. Учимся говорить о желаниях без стыда.',
                'professional_content': 'Неделя 5 - протоколы эффективной коммуникации о потребностях и границах.',
                'peer_content': 'Учимся говорить о сексе открыто! Это круче чем кажется, когда привыкнешь.',
            },
            {
                'week_number': 6,
                'theme_title': 'Техника #3 - Продление удовольствия',
                'focus_area': 'Мастерство удовольствия',
                'description': 'Продвинутые техники для продления и интенсификации удовольствия',
                'mentor_content': 'Истинное мастерство - в умении растянуть прекрасные моменты. Качество важнее количества.',
                'professional_content': 'Неделя 6 - оптимизация продолжительности и интенсивности. Техники для максимального эффекта.',
                'peer_content': 'Время для продвинутых техник! Будем учиться получать максимум удовольствия.',
            },
            {
                'week_number': 7,
                'theme_title': 'Психология отношений: attachment styles',
                'focus_area': 'Отношения и привязанность',
                'description': 'Изучение стилей привязанности и их влияния на интимность',
                'mentor_content': 'Понимание наших паттернов привязанности помогает строить более глубокие отношения.',
                'professional_content': 'Неделя 7 - анализ стилей привязанности для оптимизации отношений.',
                'peer_content': 'Разбираемся, как мы привязываемся к людям и как это влияет на наши отношения.',
            },
            {
                'week_number': 8,
                'theme_title': 'Интеграция: практики для долгосрочного развития',
                'focus_area': 'Интеграция и долгосрочное развитие',
                'description': 'Завершение курса, интеграция знаний и планирование дальнейшего развития',
                'mentor_content': 'Завершение круга. Интегрируем все изученное в целостную практику для жизни.',
                'professional_content': 'Финальная неделя - интеграция всех модулей в персональную систему развития.',
                'peer_content': 'Финал нашего путешествия! Собираем все знания вместе и планируем дальнейший путь.',
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for theme_data in weekly_themes:
            theme, created = WeeklyTheme.objects.update_or_create(
                week_number=theme_data['week_number'],
                defaults=theme_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created theme for week {theme.week_number}: {theme.theme_title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated theme for week {theme.week_number}: {theme.theme_title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nWeekly themes loaded: {created_count} created, {updated_count} updated'
            )
        )