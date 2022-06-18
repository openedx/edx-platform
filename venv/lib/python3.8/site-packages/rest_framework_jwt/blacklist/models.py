# -*- coding: utf-8 -*-

from django import VERSION
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_str

from rest_framework_jwt.settings import api_settings


class BlacklistedTokenManager(models.Manager):
    def delete_stale_tokens(self):
        return self.filter(expires_at__lt=timezone.now()).delete()


class BlacklistedToken(models.Model):
    class Meta:
        if VERSION >= (2, 2):
            constraints = [
                models.CheckConstraint(
                    check=Q(token_id__isnull=False) | Q(token__isnull=False),
                    name='token_or_id_not_null',
                )
            ]

    # This holds the original token id for refreshed tokens with ids
    token_id = models.UUIDField(db_index=True, null=True)
    token = models.TextField(db_index=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField(db_index=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    objects = BlacklistedTokenManager()

    def __str__(self):
        return 'Blacklisted token - {} - {}'.format(self.user, self.expires_at)


    @staticmethod
    def is_blocked(token, payload):
        token = force_str(token)

        # For invalidated tokens that have an original token id (orig_jti),
        # we record that in the list, so that the whole family of tokens
        # refreshed from the same initial token is rejected.
        token_id = payload.get('orig_jti') or payload.get('jti')

        if api_settings.JWT_TOKEN_ID == 'require':
            query = Q(token_id=token_id)
        elif api_settings.JWT_TOKEN_ID == 'off':
            query = Q(token=token)
        else:
            query = Q(token__isnull=False, token=token) | Q(token_id__isnull=False, token_id=token_id)

        return BlacklistedToken.objects.filter(query).exists()
