from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf.urls.static import static
from django.conf import settings

def home(request):
    return render(request, 'home.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # ✅ this connects / to your templates/home.html
    path('users/', include('users.urls')),
    path('predictions/', include('predictions.urls')),
    path('appointments/', include('appointments.urls')),
    path('analytics/', include('analytics.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('pharmacy/', include('pharmacy.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
