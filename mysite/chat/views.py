import re
from django.shortcuts import render, redirect
from .models import Chat_Message
from django.contrib import messages
from django.db.models import Q
from django.db.models import Count, Max
# Create your views here.

def chat(request):
    chat = Chat_Message.objects.values('room').annotate(count=Count('room')).filter(count__gte=5)
    return render(request, 'chat/chat.html', {'chat': chat})

def log(request):
    chat = Chat_Message.objects.values('room').annotate(count=Count('room')).filter(count__gte=5)
    chat_message_logs = Chat_Message.objects.order_by('-created_at')
    chat_message_room_logs = ''
    room_chat = ''
    """ 検索機能 """
    objects = request.GET.get('input_roomname')
    if objects:
        chat_message_room_logs = chat_message_logs.filter(
            Q(room=objects)
        )
        room_chat = 'ルーム「{}」の検索結果'.format(objects)
    return render(request, 'chat/log.html', {
        'chat_message_logs': chat_message_logs, 'chat_message_room_logs': chat_message_room_logs,
        'room_chat': room_chat, 'chat': chat
        })

def chat_log(request):
    pass
