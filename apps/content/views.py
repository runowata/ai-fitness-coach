from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Story, StoryChapter, UserStoryAccess


@login_required
def stories_list(request):
    """List all available stories"""
    # Get all published stories
    stories = Story.objects.filter(is_published=True).order_by('title')
    
    # Get user's accessible chapters
    accessible_chapters = UserStoryAccess.objects.filter(
        user=request.user
    ).select_related('chapter', 'chapter__story')
    
    # Group by story
    accessible_by_story = {}
    for access in accessible_chapters:
        story_id = access.chapter.story.id
        if story_id not in accessible_by_story:
            accessible_by_story[story_id] = []
        accessible_by_story[story_id].append(access.chapter.chapter_number)
    
    # Add accessibility info to stories
    stories_data = []
    for story in stories:
        accessible_chapters_count = len(accessible_by_story.get(story.id, []))
        stories_data.append({
            'story': story,
            'accessible_chapters': accessible_chapters_count,
            'latest_chapter': max(accessible_by_story.get(story.id, [0])),
            'is_new': accessible_chapters_count > 0
        })
    
    context = {
        'stories_data': stories_data,
        'total_accessible': sum(len(chapters) for chapters in accessible_by_story.values())
    }
    
    return render(request, 'content/stories_list.html', context)


@login_required
def story_detail(request, story_slug):
    """Show story details and chapter list"""
    story = get_object_or_404(Story, slug=story_slug, is_published=True)
    
    # Get user's accessible chapters for this story
    accessible_chapters = UserStoryAccess.objects.filter(
        user=request.user,
        chapter__story=story
    ).values_list('chapter__chapter_number', flat=True)
    
    # Get all chapters with accessibility info
    chapters = []
    for chapter in story.chapters.filter(is_published=True).order_by('chapter_number'):
        is_accessible = chapter.chapter_number in accessible_chapters
        chapters.append({
            'chapter': chapter,
            'is_accessible': is_accessible,
            'is_locked': not is_accessible
        })
    
    context = {
        'story': story,
        'chapters': chapters,
        'accessible_count': len(accessible_chapters)
    }
    
    return render(request, 'content/story_detail.html', context)


@login_required
def read_chapter(request, story_slug, chapter_number):
    """Read a specific chapter"""
    story = get_object_or_404(Story, slug=story_slug, is_published=True)
    chapter = get_object_or_404(
        StoryChapter, 
        story=story, 
        chapter_number=chapter_number,
        is_published=True
    )
    
    # Check if user has access
    try:
        access = UserStoryAccess.objects.get(
            user=request.user,
            chapter=chapter
        )
    except UserStoryAccess.DoesNotExist:
        messages.error(request, 'У вас нет доступа к этой главе. Выполните больше тренировок для разблокировки!')
        return redirect('content:story_detail', story_slug=story.slug)
    
    # Update reading stats
    if not access.first_read_at:
        access.first_read_at = timezone.now()
    access.last_read_at = timezone.now()
    access.read_count += 1
    access.save()
    
    # Get previous and next chapters
    prev_chapter = story.chapters.filter(
        chapter_number__lt=chapter_number,
        is_published=True
    ).order_by('-chapter_number').first()
    
    next_chapter = story.chapters.filter(
        chapter_number__gt=chapter_number,
        is_published=True
    ).order_by('chapter_number').first()
    
    # Check if next chapter is accessible
    next_accessible = False
    if next_chapter:
        next_accessible = UserStoryAccess.objects.filter(
            user=request.user,
            chapter=next_chapter
        ).exists()
    
    context = {
        'story': story,
        'chapter': chapter,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
        'next_accessible': next_accessible,
        'reading_time': access.read_count,
        'first_read': access.read_count == 1
    }
    
    return render(request, 'content/read_chapter.html', context)


@login_required
def unlock_preview(request, chapter_id):
    """Preview what achievement unlocks this chapter"""
    chapter = get_object_or_404(StoryChapter, id=chapter_id, is_published=True)
    
    # Find achievement that unlocks this chapter
    from apps.achievements.models import Achievement
    achievement = Achievement.objects.filter(
        unlocks_story_chapter=chapter,
        is_active=True
    ).first()
    
    if not achievement:
        return JsonResponse({'error': 'Способ разблокировки не найден'}, status=404)
    
    # Check user's progress toward this achievement
    profile = request.user.profile
    current_progress = 0
    progress_text = ""
    
    if achievement.trigger_type == 'workout_count':
        current_progress = profile.total_workouts_completed
        progress_text = "тренировок выполнено"
        
    elif achievement.trigger_type == 'streak_days':
        current_progress = profile.current_streak
        progress_text = "дней подряд"
        
    elif achievement.trigger_type == 'xp_earned':
        current_progress = profile.experience_points
        progress_text = "XP заработано"
    
    progress_percent = min(int((current_progress / achievement.trigger_value) * 100), 100)
    
    return JsonResponse({
        'achievement': {
            'name': achievement.name,
            'description': achievement.description,
            'current_progress': current_progress,
            'required_progress': achievement.trigger_value,
            'progress_percent': progress_percent,
            'progress_text': progress_text
        },
        'chapter': {
            'title': chapter.title,
            'story_title': chapter.story.title
        }
    })


@login_required
def get_next_chapter(request):
    """API endpoint to get next available chapter for the user"""
    # Get user's accessible chapters
    accessible_chapters = UserStoryAccess.objects.filter(
        user=request.user
    ).select_related('chapter', 'chapter__story').order_by('-unlocked_at')
    
    if not accessible_chapters.exists():
        return JsonResponse({'error': 'У вас пока нет доступных глав'}, status=404)
    
    # Get the most recently unlocked chapter
    latest_access = accessible_chapters.first()
    latest_chapter = latest_access.chapter
    
    # Try to find next chapter in the same story
    next_chapter = latest_chapter.story.chapters.filter(
        chapter_number__gt=latest_chapter.chapter_number,
        is_published=True
    ).order_by('chapter_number').first()
    
    # Check if user has access to next chapter
    if next_chapter:
        try:
            UserStoryAccess.objects.get(user=request.user, chapter=next_chapter)
            # User has access to next chapter
            return JsonResponse({
                'success': True,
                'next_chapter': {
                    'story_slug': next_chapter.story.slug,
                    'chapter_number': next_chapter.chapter_number,
                    'title': next_chapter.title,
                    'story_title': next_chapter.story.title,
                    'estimated_reading_time': next_chapter.estimated_reading_time,
                    'url': f'/content/stories/{next_chapter.story.slug}/{next_chapter.chapter_number}/'
                }
            })
        except UserStoryAccess.DoesNotExist:
            pass
    
    # If no next chapter in same story, find first available chapter in any story
    for access in accessible_chapters:
        chapter = access.chapter
        if not access.first_read_at:  # Unread chapter
            return JsonResponse({
                'success': True,
                'next_chapter': {
                    'story_slug': chapter.story.slug,
                    'chapter_number': chapter.chapter_number,
                    'title': chapter.title,
                    'story_title': chapter.story.title,
                    'estimated_reading_time': chapter.estimated_reading_time,
                    'url': f'/content/stories/{chapter.story.slug}/{chapter.chapter_number}/'
                }
            })
    
    # If all accessible chapters are read, return the latest one
    return JsonResponse({
        'success': True,
        'next_chapter': {
            'story_slug': latest_chapter.story.slug,
            'chapter_number': latest_chapter.chapter_number,
            'title': latest_chapter.title,
            'story_title': latest_chapter.story.title,
            'estimated_reading_time': latest_chapter.estimated_reading_time,
            'url': f'/content/stories/{latest_chapter.story.slug}/{latest_chapter.chapter_number}/',
            'is_reread': True
        }
    })