"""
Custom OAuth2 modes
"""

from django.db import models

from provider.oauth2.models import Client


class TrustedClient(models.Model):
    """
    By default `django-oauth2-provider` shows a consent form to the
    user after his credentials has been validated. Trusted clients
    bypass the user consent and redirect to the OAuth2 client
    directly.

    """
    client = models.ForeignKey(Client)
