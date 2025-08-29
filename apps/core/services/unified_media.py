"""
Унифицированный сервис для работы с медиафайлами из R2
Заменяет дублирующую функциональность MediaAsset
"""
import os
from typing import List, Optional, Dict, Any
from django.db.models import Q, QuerySet

from apps.workouts.models import R2Video, R2Image


class UnifiedMediaService:
    """
    Единый сервис для работы с медиафайлами из R2 хранилища
    Заменяет MediaAsset и дублирующие функции
    """
    
    # Базовый URL для R2
    R2_BASE_URL = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
    
    @classmethod
    def get_video_by_category_and_archetype(cls, category: str, archetype: str = None) -> QuerySet:
        """Получить видео по категории и архетипу"""
        queryset = R2Video.objects.filter(category=category)
        if archetype:
            queryset = queryset.filter(archetype=archetype)
        return queryset.order_by('sort_order', 'code')
    
    @classmethod
    def get_featured_videos(cls) -> QuerySet:
        """Получить избранные видео для landing page"""
        return R2Video.objects.filter(is_featured=True).order_by('sort_order')
    
    @classmethod
    def get_landing_images(cls) -> QuerySet:
        """Получить изображения для landing page"""
        return R2Image.objects.filter(is_featured=True).order_by('sort_order')
    
    @classmethod
    def get_hero_images(cls) -> QuerySet:
        """Получить главные изображения для hero секции"""
        return R2Image.objects.filter(is_hero_image=True).order_by('sort_order')
    
    @classmethod
    def get_avatar_for_archetype(cls, archetype: str) -> Optional[R2Image]:
        """Получить аватар для конкретного архетипа"""
        return R2Image.objects.filter(
            category='avatars',
            archetype=archetype
        ).first()
    
    @classmethod
    def get_motivational_images(cls, category: str = 'quotes') -> QuerySet:
        """Получить мотивационные изображения по категории"""
        return R2Image.objects.filter(category=category).order_by('sort_order')
    
    @classmethod
    def get_workout_videos_for_exercise(cls, exercise_type: str, archetype: str = None) -> QuerySet:
        """
        Получить видео для конкретного типа упражнения
        exercise_type: warmup, main, endurance, relaxation
        """
        videos = R2Video.objects.filter(category='exercises')
        
        # Фильтруем по типу упражнения через код видео
        if exercise_type == 'warmup':
            videos = videos.filter(code__startswith='warmup_')
        elif exercise_type in ['main', 'endurance', 'relaxation']:
            videos = videos.filter(code__startswith=f'{exercise_type}_')
        
        if archetype:
            videos = videos.filter(archetype=archetype)
            
        return videos.order_by('sort_order', 'code')
    
    @classmethod
    def get_weekly_motivation_video(cls, week_number: int, archetype: str = None) -> Optional[R2Video]:
        """Получить еженедельное мотивационное видео"""
        queryset = R2Video.objects.filter(
            category='weekly',
            code__contains=f'week{week_number:02d}'
        )
        if archetype:
            queryset = queryset.filter(archetype=archetype)
        return queryset.first()
    
    @classmethod
    def get_progress_video(cls, archetype: str = None) -> Optional[R2Video]:
        """Получить видео прогресса"""
        queryset = R2Video.objects.filter(category='progress')
        if archetype:
            queryset = queryset.filter(archetype=archetype)
        return queryset.first()
    
    @classmethod
    def get_final_video(cls, archetype: str = None) -> Optional[R2Video]:
        """Получить финальное видео"""
        queryset = R2Video.objects.filter(category='final')
        if archetype:
            queryset = queryset.filter(archetype=archetype)
        return queryset.first()
    
    @classmethod
    def get_public_url(cls, media_obj) -> str:
        """
        Получить публичный URL для медиафайла
        Заменяет content/views.py media_proxy
        """
        if hasattr(media_obj, 'r2_url'):
            return media_obj.r2_url
        return ""
    
    @classmethod
    def get_signed_url(cls, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Получить подписанный URL из R2 (для приватного контента)
        Использует те же credentials что и content/views.py
        """
        import boto3
        from botocore.exceptions import ClientError
        
        bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME")
        endpoint = os.environ.get("AWS_S3_ENDPOINT_URL")
        access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        
        if not all([bucket, endpoint, access_key, secret_key]):
            return None
        
        try:
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name="auto",
            )
            
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError:
            return None
    
    @classmethod
    def search_media(cls, query: str, media_type: str = 'all') -> Dict[str, QuerySet]:
        """
        Поиск по медиафайлам
        media_type: 'video', 'image', 'all'
        """
        results = {}
        
        if media_type in ['video', 'all']:
            results['videos'] = R2Video.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(code__icontains=query)
            ).order_by('sort_order')
        
        if media_type in ['image', 'all']:
            results['images'] = R2Image.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(code__icontains=query) |
                Q(alt_text__icontains=query)
            ).order_by('sort_order')
        
        return results
    
    @classmethod
    def get_archetype_display_name(cls, archetype: str) -> str:
        """Получить отображаемое имя архетипа"""
        archetype_names = {
            'mentor': 'Мудрый наставник',
            'professional': 'Профессиональный тренер',
            'peer': 'Лучший друг'
        }
        return archetype_names.get(archetype, archetype)
    
    @classmethod
    def get_media_stats(cls) -> Dict[str, int]:
        """Получить статистику медиафайлов"""
        return {
            'total_videos': R2Video.objects.count(),
            'total_images': R2Image.objects.count(),
            'featured_videos': R2Video.objects.filter(is_featured=True).count(),
            'featured_images': R2Image.objects.filter(is_featured=True).count(),
            'hero_images': R2Image.objects.filter(is_hero_image=True).count(),
            'videos_by_category': {
                category[0]: R2Video.objects.filter(category=category[0]).count()
                for category in R2Video.CATEGORY_CHOICES
            },
            'images_by_category': {
                category[0]: R2Image.objects.filter(category=category[0]).count() 
                for category in R2Image.CATEGORY_CHOICES
            }
        }