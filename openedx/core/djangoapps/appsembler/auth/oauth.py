"""

"""
from django.conf import settings
from django.db.models import Subquery

from oauth2_provider.models import (get_application_model,
                                    AccessToken,
                                    RefreshToken)

from .models import TrustedApplication


def destroy_oauth_tokens(user):
    """
    Destroys OAuth access and refresh tokens for the given user

    All OAuth access and refresh tokens should be destroyed unless the setting,
    'KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS' is `True`. If it is `True` then
    trusted application tokens should be preserved. These are tracked in the
    `openedx.core.djangoapps.appsembler.auth.models.TrustedApplication` model
    """
    dot_access_query = AccessToken.objects.filter(user=user.id)
    dot_refresh_query = RefreshToken.objects.filter(user=user.id)

    Application = get_application_model()

    if settings.FEATURES.get('KEEP_TRUSTED_CONFIDENTIAL_CLIENT_TOKENS', False):
        # Appsembler: Avoid deleting the trusted confidential applications such
        # as the Appsembler Management Console
        trusted_applications = Application.objects.filter(
            client_type=Application.CLIENT_CONFIDENTIAL,
            pk__in=Subquery(TrustedApplication.objects.all().values('id')),
        )

        dot_access_query = dot_access_query.exclude(
            application__in=trusted_applications)
        dot_refresh_query = dot_refresh_query.exclude(
            application__in=trusted_applications)

    # This is a quick hack fix to work around the oauth2_provider migrations
    # problem where refresh token has a non-nullable foreign key field to the
    # access token table
    # For more details see the PR:
    # https://github.com/appsembler/edx-platform/pull/883
    dot_refresh_query.delete()
    dot_access_query.delete()
