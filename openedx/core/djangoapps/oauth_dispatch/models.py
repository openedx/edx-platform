"""
Specialized models for oauth_dispatch djangoapp
"""

from datetime import datetime
from django.db import models
from pytz import utc

from oauth2_provider.settings import oauth2_settings
from oauth2_provider.models import AccessToken

# define default separator used to store lists
# IMPORTANT: Do not change this after data has been populated in database
_DEFAULT_SEPARATOR = ' '


class RestrictedApplication(models.Model):
    """
    This model lists which django-oauth-toolkit Applications are considered 'restricted'
    and thus have a limited ability to use various APIs.

    A restricted Application will only get expired token/JWT payloads
    so that they cannot be used to call into APIs.
    """

    application = models.ForeignKey(
        oauth2_settings.APPLICATION_MODEL,
        null=False,
        related_name='restricted_application'
    )

    # a space separated list of scopes that this application can request
    _allowed_scopes = models.TextField(null=True)

    # a space separated list of ORGs that this application is associated with
    # this field will be used to implement appropriate data filtering
    # so that clients of a specific OAuth2 Application will only be
    # able retrieve datasets that the OAuth2 Application is allowed to retrieve.
    _org_associations = models.TextField(null=True)

    # a space separated list of users that this application is associated with
    # this field will be used to implement appropriate data filtering
    # so that clients of a specific OAuth2 Application will only be
    # able retrieve datasets that the OAuth2 Application is allowed to retrieve.
    # OPTIONAL field if no filtering on users required
    _allowed_users = models.TextField(null=True, blank=True)

    def __unicode__(self):
        """
        Return a unicode representation of this object
        """
        return u"<RestrictedApplication '{name}'>".format(
            name=self.application.name
        )

    @classmethod
    def is_token_a_restricted_application(cls, token):
        """
        Returns if token is issued to a RestriectedApplication
        """

        if isinstance(token, basestring):
            # if string is passed in, do the look up
            token_obj = AccessToken.objects.get(token=token)
        else:
            token_obj = token

        return cls.get_restricted_application(token_obj.application) is not None

    @classmethod
    def get_restricted_application(cls, application):
        """
        For a given application, get the related restricted application
        """
        return RestrictedApplication.objects.filter(application=application.id).first()

    @classmethod
    def get_restricted_application_from_token(cls, token):
        """
        Returns a RestrictedApplication object for a token, None is none exists
        """

        if isinstance(token, basestring):
            # if string is passed in, do the look up
            # TODO: Is there a way to do this with one DB lookup?
            access_token = AccessToken.objects.select_related('application').filter(token=token).first()
            application = access_token.application
        else:
            application = token.application

        return cls.get_restricted_application(application)

    def _get_list_from_delimited_string(self, delimited_string, separator=_DEFAULT_SEPARATOR):
        """
        Helper to return a list from a delimited string
        """

        return delimited_string.split(separator) if delimited_string else []

    @property
    def allowed_scopes(self):
        """
        Translate space delimited string to a list
        """
        return self._get_list_from_delimited_string(self._allowed_scopes)

    @allowed_scopes.setter
    def allowed_scopes(self, value):
        """
        Convert list to separated string
        """
        self._allowed_scopes = _DEFAULT_SEPARATOR.join(value)

    def has_scope(self, scope):
        """
        Returns in the RestrictedApplication has the requested scope
        """

        return scope in self.allowed_scopes

    @property
    def org_associations(self):
        """
        Translate space delimited string to a list
        """
        return self._get_list_from_delimited_string(self._org_associations)

    @org_associations.setter
    def org_associations(self, value):
        """
        Convert list to separated string
        """
        self._org_associations = _DEFAULT_SEPARATOR.join(value)

    def is_associated_with_org(self, org):
        """
        Returns if the RestriectedApplication is associated with the requested org
        """

        return org in self.org_associations

    @property
    def allowed_users(self):
        """
        Translate space delimited string to a list
        """
        return self._get_list_from_delimited_string(self._allowed_users)

    @allowed_users.setter
    def allowed_users(self, value):
        """
        Convert list to separated string
        """
        self._allowed_users = _DEFAULT_SEPARATOR.join(value)

    def has_user(self, user):
        """
        Returns in the RestrictedApplication has the requested users
        """

        return user in self.allowed_users

    def has_users(self):
        """
        Returns True if users are specified in RestrictedApplication

        """
        return bool(self._get_list_from_delimited_string(self._allowed_users))

    @classmethod
    def set_access_token_as_expired(cls, access_token):
        """
        For access_tokens for RestrictedApplications, put the expire timestamp into the beginning of the epoch
        which is Jan. 1, 1970
        """
        access_token.expires = datetime(1970, 1, 1, tzinfo=utc)

    @classmethod
    def verify_access_token_as_expired(cls, access_token):
        """
        For access_tokens for RestrictedApplications, make sure that the expiry date
        is set at the beginning of the epoch which is Jan. 1, 1970
        """
        return access_token.expires == datetime(1970, 1, 1, tzinfo=utc)

    @classmethod
    def is_token_a_restricted_application(cls, token):
        """
        Returns if token is issued to a RestriectedApplication
        """

        if isinstance(token, basestring):
            # if string is passed in, do the look up
            token_obj = AccessToken.objects.get(token=token)
        else:
            token_obj = token

        return cls.get_restricted_application(token_obj.application) is not None

    @classmethod
    def get_restricted_application(cls, application):
        """
        For a given application, get the related restricted application
        """
        return RestrictedApplication.objects.filter(application=application.id).first()
