# pharmacy/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("marketplace/", views.pharmacy_marketplace, name="pharmacy_marketplace"),

    # patient side
    path("order/<int:medicine_id>/", views.place_order, name="place_order"),
    path("my-orders/", views.patient_orders, name="patient_orders"),
    path("my-orders/<int:order_id>/confirm/", views.confirm_order_received, name="confirm_order_received"),

    # pharmacy side
    path("orders/", views.pharmacy_orders, name="pharmacy_orders"),
    path('edit-profile/', views.edit_pharmacy_profile, name='edit_pharmacy_profile'),
    path('medicine/<int:medicine_id>/edit/', views.edit_medicine, name='edit_medicine'),
    path('clear-completed-orders/', views.clear_completed_orders, name='clear_completed_orders'),
    path('order/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
]
