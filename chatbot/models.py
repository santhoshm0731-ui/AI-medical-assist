from django.db import models
from django.conf import settings  # ✅ use settings.AUTH_USER_MODEL

class ChatHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ fix: this supports your custom user model
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat by {self.user or 'Guest'} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
