from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.views.decorators.http import require_GET

from apps.core.services.unified_media import UnifiedMediaService


def health(request):
    return JsonResponse({"ok": True})


@require_GET
def media_proxy(request, key: str):
    """
    Унифицированный прокси для медиафайлов из R2
    Использует UnifiedMediaService вместо дублирующей логики
    Пример: /content/media/images/avatars/peer_avatar_1.jpg
    """
    try:
        # Пытаемся получить подписанный URL через унифицированный сервис
        signed_url = UnifiedMediaService.get_signed_url(key)
        
        if signed_url:
            return HttpResponseRedirect(signed_url)
        
        # Если подписанный URL недоступен, возвращаем ошибку
        return HttpResponseBadRequest("Unable to generate signed URL for media file")
        
    except Exception as e:
        return HttpResponseBadRequest(f"Media proxy error: {str(e)}")