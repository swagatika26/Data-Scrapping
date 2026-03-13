from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.timestamp:%Y-%m-%d %H:%M:%S}"


class TrafficLog(models.Model):
    path = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.path} - {self.timestamp:%Y-%m-%d %H:%M:%S}"


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='conversations', on_delete=models.CASCADE)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='admin_conversations', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Conversation {self.pk} - {self.user_id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    message_text = models.TextField()
    message_type = models.CharField(max_length=20, default='text')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Msg {self.pk} in Conv {self.conversation_id}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name='notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, default='chat_message')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif {self.pk} for {self.user_id}"
