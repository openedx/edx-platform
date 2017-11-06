from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.models import AbstractApplication


class Application(AbstractApplication):
    """ OAuth application model.

    Allows for declared authorization grant type in addition to the client credentials grant.
    """

    class Meta(object):
        # NOTE: We use this table name to avoid issues with migrating existing data
        # and updating foreign keys for existing installations.
        db_table = 'oauth2_provider_application'

    restricted = models.BooleanField(
        default=False,
        help_text=_('Restricted clients receive expired access tokens. '
                    'They are intended to provide identity information to third-parties.')
    )

    def allows_grant_type(self, *grant_types):
        return bool({self.authorization_grant_type, self.GRANT_CLIENT_CREDENTIALS}.intersection(set(grant_types)))


# TODO Phase 3: Delete this model
class RestrictedApplication(models.Model):
    """
    This model lists which django-oauth-toolkit Applications are considered 'restricted'
    and thus have a limited ability to use various APIs.

    A restricted Application will only get expired token/JWT payloads
    so that they cannot be used to call into APIs.
    """

    application = models.ForeignKey(settings.OAUTH2_PROVIDER_APPLICATION_MODEL, null=False)
