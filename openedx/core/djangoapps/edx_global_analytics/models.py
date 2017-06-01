"""
Models for the edX global analytics application.
"""

from django.db import models


class TokenStorage(models.Model):
    """
    This model represents relationship`s key with analytics-server.

    `secret_token` is a sequence of characters as special key.
    """
    secret_token = models.CharField(max_length=255, null=True)
