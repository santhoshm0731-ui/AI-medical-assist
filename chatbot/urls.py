from django.urls import path
from . import views

urlpatterns = [
    path("", views.chatbot_home, name="chatbot_home"),
    path("get-response/", views.chatbot_reply, name="chatbot_reply"),
    path("delete-history/", views.delete_chat_history, name="delete_chat_history"),
    path("history/", views.view_chat_history, name="view_chat_history"),

]
