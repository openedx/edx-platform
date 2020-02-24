"""
Specialized models for oauth_dispatch djangoapp
"""


from datetime import datetime

import six
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_mysql.models import ListCharField
from oauth2_provider.settings import oauth2_settings
from organizations.models import Organization
from pytz import utc

from openedx.core.djangolib.markup import HTML
from openedx.core.lib.request_utils import get_request_or_stub


@python_2_unicode_compatible
class RestrictedApplication(models.Model):
    """
    This model lists which django-oauth-toolkit Applications are considered 'restricted'
    and thus have a limited ability to use various APIs.

    A restricted Application will only get expired token/JWT payloads
    so that they cannot be used to call into APIs.

    .. no_pii:
    """

    application = models.ForeignKey(oauth2_settings.APPLICATION_MODEL, null=False, on_delete=models.CASCADE)

    class Meta:
        app_label = 'oauth_dispatch'

    def __str__(self):
        """
        Return a unicode representation of this object
        """
        return HTML(u"<RestrictedApplication '{name}'>").format(
            name=HTML(self.application.name)
        )

    @classmethod
    def should_expire_access_token(cls, application):
        jwt_not_requested = get_request_or_stub().POST.get('token_type', '').lower() != 'jwt'
        restricted_application = cls.objects.filter(application=application).exists()
        return restricted_application and jwt_not_requested

    @classmethod
    def verify_access_token_as_expired(cls, access_token):
        """
        For access_tokens for RestrictedApplications, make sure that the expiry date
        is set at the beginning of the epoch which is Jan. 1, 1970
        """
        return access_token.expires == datetime(1970, 1, 1, tzinfo=utc)


@python_2_unicode_compatible
class ApplicationAccess(models.Model):
    """
    Specifies access control information for the associated Application.

    For usage details, see:
    - openedx/core/djangoapps/oauth_dispatch/docs/decisions/0007-include-organizations-in-tokens.rst

    .. no_pii:
    """

    application = models.OneToOneField(oauth2_settings.APPLICATION_MODEL, related_name='access',
                                       on_delete=models.CASCADE)
    scopes = ListCharField(
        base_field=models.CharField(max_length=32),
        size=25,
        max_length=(25 * 33),  # 25 * 32 character scopes, plus commas
        help_text=_('Comma-separated list of scopes that this application will be allowed to request.'),
    )

    filters = ListCharField(
        base_field=models.CharField(max_length=32),
        size=25,
        max_length=(25 * 33),  # 25 * 32 character filters, plus commas
        help_text=_('Comma-separated list of filters that this application will be allowed to request.'),
        null=True,
        blank=True,
    )

    class Meta:
        app_label = 'oauth_dispatch'

    @classmethod
    def get_scopes(cls, application):
        return cls.objects.get(application=application).scopes

    @classmethod
    def get_filters(cls, application):
        return cls.objects.get(application=application).filters

    def __str__(self):
        """
        Return a unicode representation of this object.
        """
        return u"{application_name}:{scopes}:{filters}".format(
            application_name=self.application.name,
            scopes=self.scopes,
            filters=self.filters,
        )


@python_2_unicode_compatible
class ApplicationOrganization(models.Model):
    """
    Associates a DOT Application to an Organization.

    See openedx/core/djangoapps/oauth_dispatch/docs/decisions/0007-include-organizations-in-tokens.rst
    for the intended use of this model.

    Deprecated: Use filters in ApplicationAccess instead.

    .. no_pii:
    """
    RELATION_TYPE_CONTENT_ORG = u'content_org'
    RELATION_TYPES = (
        (RELATION_TYPE_CONTENT_ORG, _('Content Provider')),
    )

    application = models.ForeignKey(oauth2_settings.APPLICATION_MODEL, related_name='organizations',
                                    on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    relation_type = models.CharField(
        max_length=32,
        choices=RELATION_TYPES,
        default=RELATION_TYPE_CONTENT_ORG,
    )

    class Meta:
        app_label = 'oauth_dispatch'
        unique_together = ('application', 'relation_type', 'organization')

    @classmethod
    def get_related_org_names(cls, application, relation_type=None):
        """
        Return the names of the Organizations related to the given DOT Application.

        Filter by relation_type if provided.
        """
        queryset = application.organizations.all()
        if relation_type:
            queryset = queryset.filter(relation_type=relation_type)
        return [r.organization.name for r in queryset]

    def __str__(self):
        """
        Return a unicode representation of this object.
        """
        return u"{application_name}:{organization}:{relation_type}".format(
            application_name=self.application.name,
            organization=self.organization.short_name,
            relation_type=self.relation_type,
        )

    def to_jwt_filter_claim(self):
        """
        Serialize for use in JWT filter claim.
        """
        return six.text_type(':'.join([self.relation_type, self.organization.short_name]))
