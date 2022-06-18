# -*- coding: utf-8 -*-

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BlacklistedToken
from ..settings import api_settings


@receiver(post_save, sender=BlacklistedToken)
def delete_stale_tokens(sender, **kwargs):
    if api_settings.JWT_DELETE_STALE_BLACKLISTED_TOKENS:
        BlacklistedToken.objects.delete_stale_tokens()
