import json
import logging

from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import PushNotificationLog, PushSubscription
from .serializers import PushSubscriptionSerializer

logger = logging.getLogger(__name__)


class PushSubscriptionView(generics.CreateAPIView, generics.DestroyAPIView):
    """
    POST /api/push/subscribe/ - Subscribe to push notifications
    DELETE /api/push/unsubscribe/ - Unsubscribe from push notifications
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PushSubscriptionSerializer
    
    def get_queryset(self):
        return PushSubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        subscription_id = request.data.get('subscription_id')
        if not subscription_id:
            return Response(
                {"error": "subscription_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = PushSubscription.objects.get(
                user=request.user,
                subscription_id=subscription_id
            )
            subscription.is_active = False
            subscription.save()
            
            return Response({"message": "Unsubscribed successfully"})
        except PushSubscription.DoesNotExist:
            return Response(
                {"error": "Subscription not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


@method_decorator(csrf_exempt, name='dispatch')
class OneSignalWebhookView(View):
    """
    OneSignal webhook endpoint for delivery confirmations
    POST /webhooks/onesignal/
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            event_type = data.get('event')
            
            logger.info(f"OneSignal webhook received: {event_type}")
            logger.debug(f"OneSignal webhook data: {data}")
            
            if event_type == 'notification.delivered':
                self._handle_delivered(data)
            elif event_type == 'notification.clicked':
                self._handle_clicked(data)
            else:
                logger.info(f"Unhandled OneSignal event: {event_type}")
                
            return JsonResponse({"status": "ok"})
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in OneSignal webhook")
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            logger.error(f"OneSignal webhook error: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    def _handle_delivered(self, data):
        """Handle notification delivered event"""
        notification_id = data.get('id')
        if not notification_id:
            return
            
        try:
            log = PushNotificationLog.objects.get(provider_message_id=notification_id)
            log.status = 'delivered'
            log.delivered_at = timezone.now()
            log.save()
            logger.info(f"Marked notification {notification_id} as delivered")
        except PushNotificationLog.DoesNotExist:
            logger.warning(f"Notification log not found for OneSignal ID: {notification_id}")
    
    def _handle_clicked(self, data):
        """Handle notification clicked event"""
        notification_id = data.get('id')
        if not notification_id:
            return
            
        try:
            log = PushNotificationLog.objects.get(provider_message_id=notification_id)
            log.status = 'clicked'
            log.clicked_at = timezone.now()
            log.save()
            logger.info(f"Marked notification {notification_id} as clicked")
        except PushNotificationLog.DoesNotExist:
            logger.warning(f"Notification log not found for OneSignal ID: {notification_id}")


@method_decorator(csrf_exempt, name='dispatch')
class FCMWebhookView(View):
    """
    FCM webhook endpoint (if using FCM HTTP v1 API with delivery receipts)
    POST /webhooks/fcm/
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            logger.info("FCM webhook received")
            logger.debug(f"FCM webhook data: {data}")
            
            # FCM webhook implementation depends on your specific setup
            # This is a placeholder for custom FCM delivery tracking
            
            return JsonResponse({"status": "ok"})
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in FCM webhook")
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            logger.error(f"FCM webhook error: {e}")
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def push_stats_view(request):
    """
    GET /api/push/stats/ - Get push notification statistics
    Requires staff permissions
    """
    if not request.user.is_staff:
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    from django.db.models import Count
    
    stats = {
        "total_subscriptions": PushSubscription.objects.filter(is_active=True).count(),
        "subscriptions_by_provider": dict(
            PushSubscription.objects.filter(is_active=True)
            .values('provider')
            .annotate(count=Count('id'))
            .values_list('provider', 'count')
        ),
        "subscriptions_by_platform": dict(
            PushSubscription.objects.filter(is_active=True)
            .values('platform')
            .annotate(count=Count('id'))
            .values_list('platform', 'count')
        ),
        "recent_notifications": dict(
            PushNotificationLog.objects.filter(sent_at__gte=timezone.now() - timezone.timedelta(days=7))
            .values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
    }
    
    return JsonResponse(stats)