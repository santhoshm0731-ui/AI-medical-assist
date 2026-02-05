from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/admin/', views.admin_login, name='admin_login'),


    path('login/patient/', views.patient_login, name='patient_login'),
    path('login/doctor/', views.doctor_login, name='doctor_login'),
    path('login/pharmacy/', views.pharmacy_login, name='pharmacy_login'),
    path('logout/', views.user_logout, name='logout'),


    path('register/patient/', views.register_patient, name='register_patient'),
    path('register/doctor/', views.register_doctor, name='register_doctor'),
    path('register/pharmacy/', views.register_pharmacy, name='register_pharmacy'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('pharmacy/dashboard/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('patient/profile/edit/', views.edit_patient_profile, name='edit_patient_profile'),
    path('doctor/profile/edit/', views.edit_doctor_profile, name='edit_doctor_profile'),
    ]

