from django.db import models
from django.conf import settings

class HealthRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    weight_kg = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    bp = models.CharField(max_length=10, blank=True, null=True)
    sugar = models.FloatField(null=True, blank=True)
    heartrate = models.FloatField(null=True, blank=True)
    oxygen = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"
