from django.contrib.auth.models import User
from django.db import models


class UserPreference(models.Model):
    """A user's preference, stored as generic text to be processed by client"""
    user = models.ForeignKey(User, db_index=True, related_name="+")
    key = models.CharField(max_length=255, db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ("user", "key")
