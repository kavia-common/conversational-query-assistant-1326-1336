from django.urls import path
from .views import health, chat

urlpatterns = [
    path('health/', health, name='Health'),
    path('chat/', chat, name='Chat'),
]
