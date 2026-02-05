from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_disease, name='predict_disease'),
    path('result/', views.predict_disease, name='result'),
    path('manage/', views.manage_health, name='manage_health'),
]
