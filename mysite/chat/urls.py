from django.urls import path

from .import views

app_name = 'chat'

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('log/', views.log, name='log'),
    # path('chat_log/', views.chat_log, name='chat_log'),
]