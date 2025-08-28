"""Push Notification Services"""
import logging
from typing import Dict, List

import requests
from django.conf import settings
from django.utils import timezone

from .models import PushNotificationLog, PushSubscription

logger = logging.getLogger(__name__)


class OneSignalService:
    """OneSignal push notification service"""
    
    def __init__(self):
        self.app_id = getattr(settings, 'ONESIGNAL_APP_ID', None)
        self.rest_api_key = getattr(settings, 'ONESIGNAL_REST_API_KEY', None) 
        self.base_url = "https://api.onesignal.com/notifications"
        
    def send_notification(self, subscription: PushSubscription, title: str, body: str, data: Dict = None) -> Dict:
        """Send push notification via OneSignal"""
        if not self.app_id or not self.rest_api_key:
            logger.error("OneSignal credentials not configured")
            return {"success": False, "error": "OneSignal credentials missing"}
            
        # Log the attempt
        log = PushNotificationLog.objects.create(
            subscription=subscription,
            title=title,
            body=body,
            data=data or {},
            status='pending'
        )
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {self.rest_api_key}"
        }
        
        payload = {
            "app_id": self.app_id,
            "include_player_ids": [subscription.subscription_id],
            "headings": {"en": title},
            "contents": {"en": body},
            "data": data or {}
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("id"):
                log.status = 'sent'
                log.provider_message_id = response_data["id"]
                logger.info(f"OneSignal notification sent: {response_data['id']}")
                success = True
            else:
                log.status = 'failed'
                log.error_message = str(response_data)
                logger.error(f"OneSignal send failed: {response_data}")
                success = False
                
            log.save()
            
            return {
                "success": success,
                "provider_message_id": response_data.get("id"),
                "response": response_data
            }
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            logger.error(f"OneSignal request exception: {e}")
            return {"success": False, "error": str(e)}


class FCMService:
    """Firebase Cloud Messaging service"""
    
    def __init__(self):
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.base_url = "https://fcm.googleapis.com/fcm/send"
    
    def send_notification(self, subscription: PushSubscription, title: str, body: str, data: Dict = None) -> Dict:
        """Send push notification via FCM"""
        if not self.server_key:
            logger.error("FCM server key not configured")
            return {"success": False, "error": "FCM server key missing"}
            
        # Log the attempt
        log = PushNotificationLog.objects.create(
            subscription=subscription,
            title=title,
            body=body,
            data=data or {},
            status='pending'
        )
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={self.server_key}"
        }
        
        payload = {
            "to": subscription.subscription_id,
            "notification": {
                "title": title,
                "body": body
            },
            "data": data or {}
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("success", 0) > 0:
                log.status = 'sent'
                if response_data.get("results"):
                    log.provider_message_id = str(response_data["results"][0].get("message_id", ""))
                logger.info("FCM notification sent successfully")
                success = True
            else:
                log.status = 'failed'
                log.error_message = str(response_data)
                logger.error(f"FCM send failed: {response_data}")
                success = False
                
            log.save()
            
            return {
                "success": success,
                "provider_message_id": log.provider_message_id,
                "response": response_data
            }
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            logger.error(f"FCM request exception: {e}")
            return {"success": False, "error": str(e)}


class PushNotificationService:
    """Main push notification service"""
    
    def __init__(self):
        self.onesignal = OneSignalService()
        self.fcm = FCMService()
    
    def send_to_user(self, user, title: str, body: str, data: Dict = None) -> List[Dict]:
        """Send push notification to all user's active subscriptions"""
        if not user.profile.push_notifications_enabled:
            logger.info(f"Push notifications disabled for user {user.username}")
            return []
            
        subscriptions = user.push_subscriptions.filter(is_active=True)
        results = []
        
        for subscription in subscriptions:
            if subscription.provider == 'onesignal':
                result = self.onesignal.send_notification(subscription, title, body, data)
            elif subscription.provider == 'fcm':
                result = self.fcm.send_notification(subscription, title, body, data)
            else:
                logger.error(f"Unknown provider: {subscription.provider}")
                continue
                
            results.append({
                "subscription_id": subscription.subscription_id,
                "provider": subscription.provider,
                **result
            })
            
            # Update last_used_at if successful
            if result.get("success"):
                subscription.last_used_at = timezone.now()
                subscription.save(update_fields=['last_used_at'])
        
        return results
    
    def send_weekly_lesson_notification(self, weekly_notification) -> List[Dict]:
        """Send push notification for new weekly lesson"""
        title = f"📚 Новый урок: {weekly_notification.lesson_title}"
        body = "Изучайте новые техники и развивайтесь вместе с тренером!"
        
        data = {
            "type": "weekly_lesson",
            "week": weekly_notification.week,
            "archetype": weekly_notification.archetype,
            "notification_id": weekly_notification.id
        }
        
        return self.send_to_user(weekly_notification.user, title, body, data)
    
    def bulk_send_weekly_lessons(self, weekly_notifications) -> Dict:
        """Send push notifications for multiple weekly lessons"""
        total_sent = 0
        total_failed = 0
        
        for notification in weekly_notifications:
            try:
                results = self.send_weekly_lesson_notification(notification)
                sent_count = sum(1 for r in results if r.get("success"))
                failed_count = len(results) - sent_count
                
                total_sent += sent_count
                total_failed += failed_count
                
                logger.info(f"Weekly lesson notification for {notification.user.username}: {sent_count} sent, {failed_count} failed")
                
            except Exception as e:
                total_failed += 1
                logger.error(f"Failed to send weekly lesson notification to {notification.user.username}: {e}")
        
        return {
            "total_sent": total_sent,
            "total_failed": total_failed
        }