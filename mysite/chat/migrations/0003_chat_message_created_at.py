# Generated by Django 4.0.4 on 2022-04-21 06:57

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_chat_message_room'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat_message',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
