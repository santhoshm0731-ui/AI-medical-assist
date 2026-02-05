# pharmacy/models.py
from django.db import models
from django.conf import settings
from users.models import PharmacyProfile, Medicine  # ✅ from users.models

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('OUT_FOR_DELIVERY', 'Out for delivery'),
        ('DELIVERED', 'Delivered (awaiting confirmation)'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pharmacy_orders'
    )
    pharmacy = models.ForeignKey(
        PharmacyProfile,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,  # ✅ allow null now
        blank=True
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(
        max_length=10,
        choices=[('COD', 'Cash on Delivery'), ('UPI', 'UPI')]
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    patient_confirmed = models.BooleanField(default=False)  # ✅ patient confirmation flag

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.medicine.name} for {self.patient.username}"
