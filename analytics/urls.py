from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('download/', views.download_health_report, name='download_health_report'),
    path('clear/', views.clear_health_records, name='clear_health_records'),
    path('admin-dashboard/', views.admin_analytics_dashboard, name='admin_analytics_dashboard'),
    path('view_patients/', views.view_all_patients, name='view_all_patients'),
    path('view_doctors/', views.view_all_doctors, name='view_all_doctors'),
    path('view_pharmacies/', views.view_all_pharmacies, name='view_all_pharmacies'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]
