"""
Models for philu_commands app
"""
from django.db import models


class CreationFailedUsers(models.Model):
    """
    Model containing information about users which fail creation when command 'create_nodebb_users' is run.
    """
    email = models.EmailField(blank=False)
    is_created = models.BooleanField(default=False)
    is_activated = models.BooleanField(default=False)
