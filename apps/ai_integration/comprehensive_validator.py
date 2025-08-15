"""
Валидатор для полного 4-блочного отчета ИИ
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from apps.core.services.exercise_validation import ExerciseValidationService

from .schemas import (
    ComprehensiveAIReport,
)
from .validators import WorkoutPlanValidator

logger = logging.getLogger(__name__)


class ComprehensiveReportValidator:
    """Валидатор для полного 4-блочного отчета ИИ согласно эталонным документам"""
    
    def __init__(self):
        self.workout_validator = WorkoutPlanValidator()
        self.validation_service = ExerciseValidationService()
        self.issues_found = []
        self.fixes_applied = []
    
    def validate_and_fix_comprehensive_report(
        self, 
        report_data: Dict[str, Any], 
        user_id: str = None,
        archetype: str = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Валидация и исправление полного 4-блочного отчета
        
        Args:
            report_data: Данные отчета от ИИ
            user_id: ID пользователя для метаданных
            archetype: Архетип тренера
            
        Returns:
            Tuple of (исправленный_отчет, отчет_валидации)
        """
        self.issues_found = []
        self.fixes_applied = []
        
        try:
            logger.info("Начинается валидация полного отчета ИИ")
            
            # Проверяем и исправляем структуру верхнего уровня
            fixed_report = self._ensure_base_structure(report_data, user_id, archetype)
            
            # Валидируем каждый блок отдельно
            fixed_report = self._validate_user_analysis_block(fixed_report)
            fixed_report = self._validate_training_program_block(fixed_report)
            fixed_report = self._validate_motivation_system_block(fixed_report)
            fixed_report = self._validate_long_term_strategy_block(fixed_report)
            
            # Исправляем типы данных для Pydantic валидации
            fixed_report = self._fix_data_types(fixed_report)
            
            # Финальная валидация через Pydantic
            try:
                ComprehensiveAIReport.model_validate(fixed_report)
                logger.info("Pydantic валидация пройдена успешно")
            except Exception as e:
                logger.error(f"Ошибка Pydantic валидации: {e}")
                self.issues_found.append(f"Pydantic validation failed: {str(e)}")
                # Возвращаем исправленные данные даже если Pydantic не прошел
                
            # Создаем отчет валидации
            validation_report = {
                'valid': len(self.issues_found) == 0,
                'issues_found': len(self.issues_found),
                'fixes_applied': len(self.fixes_applied),
                'issues': self.issues_found,
                'fixes': self.fixes_applied,
                'structure': 'comprehensive_4_block',
                'validation_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Валидация отчета завершена: {validation_report['issues_found']} проблем, {validation_report['fixes_applied']} исправлений")
            return fixed_report, validation_report
            
        except Exception as e:
            logger.error(f"Критическая ошибка валидации отчета: {e}")
            return report_data, {
                'valid': False,
                'error': str(e),
                'issues_found': 1,
                'fixes_applied': 0,
                'structure': 'validation_failed'
            }
    
    def _ensure_base_structure(
        self, 
        report_data: Dict[str, Any], 
        user_id: str = None,
        archetype: str = None
    ) -> Dict[str, Any]:
        """Обеспечивает базовую 4-блочную структуру"""
        
        # Инициализируем meta блок
        if 'meta' not in report_data:
            report_data['meta'] = {}
            self.fixes_applied.append("Добавлен отсутствующий meta блок")
        
        meta = report_data['meta']
        if 'version' not in meta:
            meta['version'] = 'v2_comprehensive'
            self.fixes_applied.append("Добавлена версия схемы в meta")
        
        if 'generation_date' not in meta:
            meta['generation_date'] = datetime.now().isoformat()
            self.fixes_applied.append("Добавлена дата генерации в meta")
            
        if 'archetype' not in meta and archetype:
            meta['archetype'] = archetype
            self.fixes_applied.append(f"Добавлен архетип {archetype} в meta")
            
        if 'user_id' not in meta and user_id:
            meta['user_id'] = str(user_id)  # Анонимизированный ID
            self.fixes_applied.append("Добавлен user_id в meta")
        
        # Обеспечиваем наличие всех 4 блоков
        required_blocks = ['user_analysis', 'training_program', 'motivation_system', 'long_term_strategy']
        for block in required_blocks:
            if block not in report_data:
                report_data[block] = {}
                self.fixes_applied.append(f"Добавлен отсутствующий блок {block}")
                self.issues_found.append(f"Отсутствовал обязательный блок {block}")
        
        return report_data
    
    def _validate_user_analysis_block(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует БЛОК 1: Анализ пользователя"""
        analysis = report_data.get('user_analysis', {})
        
        # Обязательные поля блока анализа
        required_fields = {
            'fitness_level_assessment': 'Детальный анализ уровня физической подготовки пользователя на основе ответов онбординга.',
            'psychological_profile': 'Психологический профиль пользователя, включая мотивационные особенности и отношение к фитнесу.',
            'interaction_strategy': 'Выбранная стратегия взаимодействия с пользователем, адаптированная под его особенности.',
            'archetype_adaptation': 'Обоснование выбора и адаптации архетипа тренера под данного пользователя.'
        }
        
        for field, default_text in required_fields.items():
            if field not in analysis or not analysis[field] or len(str(analysis[field]).strip()) < 30:
                analysis[field] = default_text
                self.fixes_applied.append(f"Добавлен недостающий {field} в блок анализа пользователя")
                self.issues_found.append(f"Недостаточно данных в поле {field}")
        
        # Проверяем ограничения
        if 'limitations_analysis' not in analysis:
            analysis['limitations_analysis'] = 'На основе предоставленных данных специфических ограничений не выявлено. Рекомендуется стандартная осторожность при выполнении новых упражнений.'
            self.fixes_applied.append("Добавлен анализ ограничений")
        
        report_data['user_analysis'] = analysis
        return report_data
    
    def _validate_training_program_block(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует БЛОК 2: Программа тренировок"""
        training_program = report_data.get('training_program', {})
        
        # Используем существующий валидатор для программы тренировок
        if training_program:
            try:
                fixed_program, validation_report = self.workout_validator.validate_and_fix_plan(training_program)
                report_data['training_program'] = fixed_program
                
                # Добавляем информацию о исправлениях
                if validation_report.get('fixes_applied', 0) > 0:
                    self.fixes_applied.extend([f"Программа тренировок: {fix}" for fix in validation_report.get('fixes', [])])
                if validation_report.get('issues_found', 0) > 0:
                    self.issues_found.extend([f"Программа тренировок: {issue}" for issue in validation_report.get('issues', [])])
                    
            except Exception as e:
                logger.error(f"Ошибка валидации программы тренировок: {e}")
                self.issues_found.append(f"Критическая ошибка в программе тренировок: {str(e)}")
        else:
            self.issues_found.append("Отсутствует программа тренировок")
            # Создаем минимальную программу как fallback
            report_data['training_program'] = {
                'plan_name': 'Персональная программа тренировок',
                'duration_weeks': 4,
                'goal': 'Улучшение физической формы и развитие уверенности в себе',
                'weeks': []
            }
            self.fixes_applied.append("Создана базовая программа тренировок")
        
        return report_data
    
    def _validate_motivation_system_block(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует БЛОК 3: Система мотивации"""
        motivation = report_data.get('motivation_system', {})
        
        required_fields = {
            'psychological_support': 'План психологической поддержки включает регулярные проверки прогресса, позитивное подкрепление достижений и работу с возможными сомнениями или барьерами.',
            'reward_system': 'Система наград основана на достижении промежуточных целей: еженедельные достижения, месячные вехи, и система внутренних поощрений за постоянство.',
            'confidence_building': 'Стратегия развития уверенности включает ежедневные задания на самопринятие, работу с образом тела и развитие позитивного отношения к себе.'
        }
        
        for field, default_text in required_fields.items():
            if field not in motivation or not motivation[field] or len(str(motivation[field]).strip()) < 50:
                motivation[field] = default_text
                self.fixes_applied.append(f"Добавлен недостающий {field} в систему мотивации")
        
        if 'community_integration' not in motivation:
            motivation['community_integration'] = 'Поощряется участие в поддерживающих онлайн-сообществах и поиск единомышленников для совместных тренировок.'
            self.fixes_applied.append("Добавлен план интеграции с сообществом")
        
        report_data['motivation_system'] = motivation
        return report_data
    
    def _validate_long_term_strategy_block(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует БЛОК 4: Долгосрочная стратегия"""
        strategy = report_data.get('long_term_strategy', {})
        
        required_fields = {
            'progression_plan': 'План прогрессии предусматривает поэтапное увеличение нагрузок, введение новых упражнений каждые 4-6 недель и развитие от базовых к более сложным движениям.',
            'adaptation_triggers': 'Основные триггеры для адаптации: плато в прогрессе, изменение целей пользователя, появление новых ограничений или значительные изменения в расписании.',
            'lifestyle_integration': 'Интеграция тренировок в образ жизни включает создание устойчивых привычек, адаптацию под рабочий график и постепенное включение активности в повседневные дела.',
            'success_metrics': 'Ключевые метрики успеха: постоянство тренировок, улучшение самочувствия, прогресс в выполнении упражнений и повышение уровня уверенности в себе.'
        }
        
        for field, default_text in required_fields.items():
            if field not in strategy or not strategy[field] or len(str(strategy[field]).strip()) < 30:
                strategy[field] = default_text
                self.fixes_applied.append(f"Добавлен недостающий {field} в долгосрочную стратегию")
        
        report_data['long_term_strategy'] = strategy
        return report_data
    
    def _fix_data_types(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Исправляет типы данных для соответствия Pydantic схемам"""
        
        # Исправляем training_program если он есть
        if 'training_program' in report_data and report_data['training_program']:
            training_program = report_data['training_program']
            
            # Преобразуем plan_name в name если присутствует
            if 'plan_name' in training_program and 'name' not in training_program:
                training_program['name'] = training_program['plan_name']
                del training_program['plan_name']
                self.fixes_applied.append("Преобразован plan_name в name")
            
            # Исправляем duration_weeks - должен быть integer
            if 'duration_weeks' in training_program:
                try:
                    if isinstance(training_program['duration_weeks'], str):
                        training_program['duration_weeks'] = int(training_program['duration_weeks'])
                        self.fixes_applied.append("Преобразован duration_weeks из строки в integer")
                except (ValueError, TypeError):
                    training_program['duration_weeks'] = 4  # Fallback
                    self.fixes_applied.append("Установлен fallback duration_weeks = 4")
                    self.issues_found.append("Некорректное значение duration_weeks")
            
            # Исправляем week_number - должен быть integer
            if 'weeks' in training_program:
                for week in training_program.get('weeks', []):
                    if 'week_number' in week:
                        try:
                            if isinstance(week['week_number'], str):
                                week['week_number'] = int(week['week_number'])
                                self.fixes_applied.append(f"Преобразован week_number из строки в integer")
                        except (ValueError, TypeError):
                            week['week_number'] = 1  # Fallback
                            self.fixes_applied.append("Установлен fallback week_number = 1")
                    
                    # Исправляем day_number - должен быть integer
                    for day in week.get('days', []):
                        if 'day_number' in day:
                            try:
                                if isinstance(day['day_number'], str):
                                    day['day_number'] = int(day['day_number'])
                                    self.fixes_applied.append(f"Преобразован day_number из строки в integer")
                            except (ValueError, TypeError):
                                day['day_number'] = 1  # Fallback
                                self.fixes_applied.append("Установлен fallback day_number = 1")
                        
                        # Исправляем sets в упражнениях - должен быть integer
                        for block in day.get('blocks', []):
                            for exercise in block.get('exercises', []):
                                if 'sets' in exercise:
                                    try:
                                        if isinstance(exercise['sets'], str):
                                            exercise['sets'] = int(exercise['sets'])
                                            self.fixes_applied.append(f"Преобразован sets из строки в integer")
                                    except (ValueError, TypeError):
                                        exercise['sets'] = 3  # Fallback
                                        self.fixes_applied.append("Установлен fallback sets = 3")
                                
                                # Исправляем rest_seconds - должен быть integer
                                if 'rest_seconds' in exercise:
                                    try:
                                        if isinstance(exercise['rest_seconds'], str):
                                            exercise['rest_seconds'] = int(exercise['rest_seconds'])
                                            self.fixes_applied.append(f"Преобразован rest_seconds из строки в integer")
                                    except (ValueError, TypeError):
                                        exercise['rest_seconds'] = 60  # Fallback
                                        self.fixes_applied.append("Установлен fallback rest_seconds = 60")
                                
                                # Исправляем duration_seconds - должен быть integer
                                if 'duration_seconds' in exercise:
                                    try:
                                        if isinstance(exercise['duration_seconds'], str):
                                            exercise['duration_seconds'] = int(exercise['duration_seconds'])
                                            self.fixes_applied.append(f"Преобразован duration_seconds из строки в integer")
                                    except (ValueError, TypeError):
                                        exercise['duration_seconds'] = 30  # Fallback
                                        self.fixes_applied.append("Установлен fallback duration_seconds = 30")
        
        return report_data
    
    def dry_run_validation(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Предварительная валидация без изменений данных
        
        Returns:
            Отчет о валидации без применения исправлений
        """
        original_report = json.loads(json.dumps(report_data))  # Deep copy
        _, validation_report = self.validate_and_fix_comprehensive_report(original_report)
        return validation_report