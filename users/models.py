from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_pharmacy = models.BooleanField(default=False)  # 🆕 pharmacy role flag


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.user.username


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100, blank=True)
    fees = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.specialty})"


class PharmacyProfile(models.Model):   # 🆕 new / already existing – extend it
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pharmacy_name = models.CharField(max_length=150)
    address = models.TextField(blank=True, null=True)

    # ✅ NEW: Payment details
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    upi_qr = models.ImageField(upload_to='upi_qr/', blank=True, null=True)

    def __str__(self):
        return self.pharmacy_name



class Medicine(models.Model):         # 🆕 new
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='medicine_images/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.pharmacy.pharmacy_name})"
