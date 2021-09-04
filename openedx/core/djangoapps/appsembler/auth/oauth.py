"""
Tests for the OAuth helper.
"""

from oauth2_provider.models import (
    AccessToken,
    RefreshToken,
)


from openedx.core.djangoapps.appsembler.sites.utils import get_amc_oauth_app


def destroy_oauth_tokens_excluding_amc_tokens(user):
    """
    Destroys OAuth access and refresh tokens for the given user.

    All OAuth access and refresh tokens should be destroyed unless the setting,
    'KEEP_AMC_TOKENS_ON_PASSWORD_RESET' is `True`. If it is `True` then
    AMC Application access and refresh tokens should be preserved.
    """
    dot_access_query = AccessToken.objects.filter(user=user.id)
    dot_refresh_query = RefreshToken.objects.filter(user=user.id)

    dot_access_query = dot_access_query.exclude(
        application=get_amc_oauth_app())
    dot_refresh_query = dot_refresh_query.exclude(
        application=get_amc_oauth_app())

    dot_refresh_query.delete()
    dot_access_query.delete()
