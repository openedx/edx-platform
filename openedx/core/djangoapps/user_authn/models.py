from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.db import models

class LoggedInUser(models.Model):
    user = models.OneToOneField(User, related_name='logged_in_user', on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
