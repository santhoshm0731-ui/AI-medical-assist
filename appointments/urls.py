from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('manage/<int:appointment_id>/<str:action>/', views.manage_appointment, name='manage_appointment'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment_patient, name='cancel_appointment_patient'),
    path("chat/<int:appointment_id>/", views.chat_view, name="chat_with_doctor"),
    path("chat/send/<int:appointment_id>/", views.send_message, name="send_chat_message"),
    path("clear-completed/patient/", views.clear_completed_patient, name="clear_completed_patient"),
    path("clear-completed/doctor/", views.clear_completed_doctor, name="clear_completed_doctor"),

]
