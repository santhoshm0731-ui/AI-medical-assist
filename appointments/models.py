

from django.db import models
from django.conf import settings

class Appointment(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_appointments')

    date = models.DateField()
    status = models.CharField(max_length=50, default='Pending')

    def __str__(self):
        return f"{self.patient} → {self.doctor} on {self.date}"

class AppointmentMessage(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    sender = models.ForeignKey(        # 🔥 use AUTH_USER_MODEL instead of User
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"Msg by {self.sender} on {self.appointment} at {self.timestamp}"

