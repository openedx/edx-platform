import uuid 
from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User 


class ChatbotSession(TimeStampedModel):
    """
    Lưu session chat bot của học viên
    """

    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='chatbot_sessions')


class ChatbotQuery(TimeStampedModel):
    """
    Lưu conversation của học viên và chatbot
    """

    STATUS_CHOICES = [
        ('idle', 'Idle'), 
        ('pending', 'Pending'), 
        ('failed', 'Failed'), 
        ('succeeded', 'Succeeded'),
        ('canceled', 'Canceled'),
    ]

    VOTE_CHOICES = [
        ('up', 'Up'), 
        ('down', 'Down'),
    ]

    id = models.AutoField(primary_key=True)

    session = models.ForeignKey(ChatbotSession, verbose_name="Chatbot Session", on_delete=models.CASCADE, related_name='chatbot_queries')

    query_msg = models.TextField(null=False)

    response_msg = models.TextField(null=True)

    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default='pending') 

    vote = models.CharField(max_length=4, choices=VOTE_CHOICES, null=True) 


