from django.db import models
import uuid
from django.utils import timezone
# Create your models here.

class Chat_Message(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.CharField('ルーム', blank=True, max_length=50)
    message = models.TextField('メッセージ', blank=True, max_length=255)
    created_at = models.DateTimeField('作成日', default=timezone.now)

    

    class Meta:
        db_table = 'chat_message'

    