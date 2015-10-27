# -*- coding: utf-8 -*-
"""
Models used to implement SAML SSO support in third_party_auth
(inlcuding Shibboleth support)
"""
from __future__ import absolute_import

from config_models.models import ConfigurationModel, cache
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import json
import logging
from provider.utils import long_token
from provider.oauth2.models import Client
from social.backends.base import BaseAuth
from social.backends.oauth import OAuthAuth
from social.backends.saml import SAMLAuth, SAMLIdentityProvider
from .lti import LTIAuthBackend, LTI_PARAMS_KEY
from social.exceptions import SocialAuthBaseException
from social.utils import module_member

log = logging.getLogger(__name__)


# A dictionary of {name: class} entries for each python-social-auth backend available.
# Because this setting can specify arbitrary code to load and execute, it is set via
# normal Django settings only and cannot be changed at runtime:
def _load_backend_classes(base_class=BaseAuth):
    """ Load the list of python-social-auth backend classes from Django settings """
    for class_path in settings.AUTHENTICATION_BACKENDS:
        auth_class = module_member(class_path)
        if issubclass(auth_class, base_class):
            yield auth_class
_PSA_BACKENDS = {backend_class.name: backend_class for backend_class in _load_backend_classes()}
_PSA_OAUTH2_BACKENDS = [backend_class.name for backend_class in _load_backend_classes(OAuthAuth)]
_PSA_SAML_BACKENDS = [backend_class.name for backend_class in _load_backend_classes(SAMLAuth)]
_LTI_BACKENDS = [backend_class.name for backend_class in _load_backend_classes(LTIAuthBackend)]


def clean_json(value, of_type):
    """ Simple helper method to parse and clean JSON """
    if not value.strip():
        return json.dumps(of_type())
    try:
        value_python = json.loads(value)
    except ValueError as err:
        raise ValidationError("Invalid JSON: {}".format(err.message))
    if not isinstance(value_python, of_type):
        raise ValidationError("Expected a JSON {}".format(of_type))
    return json.dumps(value_python, indent=4)


class AuthNotConfigured(SocialAuthBaseException):
    """ Exception when SAMLProviderData or other required info is missing """
    def __init__(self, provider_name):
        super(AuthNotConfigured, self).__init__()
        self.provider_name = provider_name

    def __str__(self):
        return _('Authentication with {} is currently unavailable.').format(  # pylint: disable=no-member
            self.provider_name
        )


class ProviderConfig(ConfigurationModel):
    """
    Abstract Base Class for configuring a third_party_auth provider
    """
    icon_class = models.CharField(
        max_length=50, default='fa-sign-in',
        help_text=(
            'The Font Awesome (or custom) icon class to use on the login button for this provider. '
            'Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university'
        ),
    )
    name = models.CharField(max_length=50, blank=False, help_text="Name of this provider (shown to users)")
    secondary = models.BooleanField(
        default=False,
        help_text=_(
            'Secondary providers are displayed less prominently, '
            'in a separate list of "Institution" login providers.'
        ),
    )
    skip_registration_form = models.BooleanField(
        default=False,
        help_text=_(
            "If this option is enabled, users will not be asked to confirm their details "
            "(name, email, etc.) during the registration process. Only select this option "
            "for trusted providers that are known to provide accurate user information."
        ),
    )
    skip_email_verification = models.BooleanField(
        default=False,
        help_text=_(
            "If this option is selected, users will not be required to confirm their "
            "email, and their account will be activated immediately upon registration."
        ),
    )
    prefix = None  # used for provider_id. Set to a string value in subclass
    backend_name = None  # Set to a field or fixed value in subclass
    accepts_logins = True  # Whether to display a sign-in button when the provider is enabled

    # "enabled" field is inherited from ConfigurationModel

    class Meta(object):
        abstract = True

    @property
    def provider_id(self):
        """ Unique string key identifying this provider. Must be URL and css class friendly. """
        assert self.prefix is not None
        return "-".join((self.prefix, ) + tuple(getattr(self, field) for field in self.KEY_FIELDS))

    @property
    def backend_class(self):
        """ Get the python-social-auth backend class used for this provider """
        return _PSA_BACKENDS[self.backend_name]

    def get_url_params(self):
        """ Get a dict of GET parameters to append to login links for this provider """
        return {}

    def is_active_for_pipeline(self, pipeline):
        """ Is this provider being used for the specified pipeline? """
        return self.backend_name == pipeline['backend']

    def match_social_auth(self, social_auth):
        """ Is this provider being used for this UserSocialAuth entry? """
        return self.backend_name == social_auth.provider

    def get_remote_id_from_social_auth(self, social_auth):
        """ Given a UserSocialAuth object, return the remote ID used by this provider. """
        # This is generally the same thing as the UID, expect when one backend is used for multiple providers
        assert self.match_social_auth(social_auth)
        return social_auth.uid

    def get_social_auth_uid(self, remote_id):
        """
        Return the uid in social auth.

        This is default implementation. Subclass may override with a different one.
        """
        return remote_id

    @classmethod
    def get_register_form_data(cls, pipeline_kwargs):
        """Gets dict of data to display on the register form.

        common.djangoapps.student.views.register_user uses this to populate the
        new account creation form with values supplied by the user's chosen
        provider, preventing duplicate data entry.

        Args:
            pipeline_kwargs: dict of string -> object. Keyword arguments
                accumulated by the pipeline thus far.

        Returns:
            Dict of string -> string. Keys are names of form fields; values are
            values for that field. Where there is no value, the empty string
            must be used.
        """
        # Details about the user sent back from the provider.
        details = pipeline_kwargs.get('details')

        # Get the username separately to take advantage of the de-duping logic
        # built into the pipeline. The provider cannot de-dupe because it can't
        # check the state of taken usernames in our system. Note that there is
        # technically a data race between the creation of this value and the
        # creation of the user object, so it is still possible for users to get
        # an error on submit.
        suggested_username = pipeline_kwargs.get('username')

        return {
            'email': details.get('email', ''),
            'name': details.get('fullname', ''),
            'username': suggested_username,
        }

    def get_authentication_backend(self):
        """Gets associated Django settings.AUTHENTICATION_BACKEND string."""
        return '{}.{}'.format(self.backend_class.__module__, self.backend_class.__name__)


class OAuth2ProviderConfig(ProviderConfig):
    """
    Configuration Entry for an OAuth2 based provider.
    Also works for OAuth1 providers.
    """
    prefix = 'oa2'
    KEY_FIELDS = ('backend_name', )  # Backend name is unique
    backend_name = models.CharField(
        max_length=50, choices=[(name, name) for name in _PSA_OAUTH2_BACKENDS], blank=False, db_index=True,
        help_text=(
            "Which python-social-auth OAuth2 provider backend to use. "
            "The list of backend choices is determined by the THIRD_PARTY_AUTH_BACKENDS setting."
            # To be precise, it's set by AUTHENTICATION_BACKENDS - which aws.py sets from THIRD_PARTY_AUTH_BACKENDS
        )
    )
    key = models.TextField(blank=True, verbose_name="Client ID")
    secret = models.TextField(
        blank=True,
        verbose_name="Client Secret",
        help_text=(
            'For increased security, you can avoid storing this in your database by leaving '
            ' this field blank and setting '
            'SOCIAL_AUTH_OAUTH_SECRETS = {"(backend name)": "secret", ...} '
            'in your instance\'s Django settings (or lms.auth.json)'
        )
    )
    other_settings = models.TextField(blank=True, help_text="Optional JSON object with advanced settings, if any.")

    class Meta(object):
        verbose_name = "Provider Configuration (OAuth)"
        verbose_name_plural = verbose_name

    def clean(self):
        """ Standardize and validate fields """
        super(OAuth2ProviderConfig, self).clean()
        self.other_settings = clean_json(self.other_settings, dict)

    def get_setting(self, name):
        """ Get the value of a setting, or raise KeyError """
        if name == "KEY":
            return self.key
        if name == "SECRET":
            if self.secret:
                return self.secret
            # To allow instances to avoid storing secrets in the DB, the secret can also be set via Django:
            return getattr(settings, 'SOCIAL_AUTH_OAUTH_SECRETS', {}).get(self.backend_name, '')
        if self.other_settings:
            other_settings = json.loads(self.other_settings)
            assert isinstance(other_settings, dict), "other_settings should be a JSON object (dictionary)"
            return other_settings[name]
        raise KeyError


class SAMLProviderConfig(ProviderConfig):
    """
    Configuration Entry for a SAML/Shibboleth provider.
    """
    prefix = 'saml'
    KEY_FIELDS = ('idp_slug', )
    backend_name = models.CharField(
        max_length=50, default='tpa-saml', choices=[(name, name) for name in _PSA_SAML_BACKENDS], blank=False,
        help_text="Which python-social-auth provider backend to use. 'tpa-saml' is the standard edX SAML backend.")
    idp_slug = models.SlugField(
        max_length=30, db_index=True,
        help_text=(
            'A short string uniquely identifying this provider. '
            'Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"'
        ))
    entity_id = models.CharField(
        max_length=255, verbose_name="Entity ID", help_text="Example: https://idp.testshib.org/idp/shibboleth")
    metadata_source = models.CharField(
        max_length=255,
        help_text=(
            "URL to this provider's XML metadata. Should be an HTTPS URL. "
            "Example: https://www.testshib.org/metadata/testshib-providers.xml"
        ))
    attr_user_permanent_id = models.CharField(
        max_length=128, blank=True, verbose_name="User ID Attribute",
        help_text="URN of the SAML attribute that we can use as a unique, persistent user ID. Leave blank for default.")
    attr_full_name = models.CharField(
        max_length=128, blank=True, verbose_name="Full Name Attribute",
        help_text="URN of SAML attribute containing the user's full name. Leave blank for default.")
    attr_first_name = models.CharField(
        max_length=128, blank=True, verbose_name="First Name Attribute",
        help_text="URN of SAML attribute containing the user's first name. Leave blank for default.")
    attr_last_name = models.CharField(
        max_length=128, blank=True, verbose_name="Last Name Attribute",
        help_text="URN of SAML attribute containing the user's last name. Leave blank for default.")
    attr_username = models.CharField(
        max_length=128, blank=True, verbose_name="Username Hint Attribute",
        help_text="URN of SAML attribute to use as a suggested username for this user. Leave blank for default.")
    attr_email = models.CharField(
        max_length=128, blank=True, verbose_name="Email Attribute",
        help_text="URN of SAML attribute containing the user's email address[es]. Leave blank for default.")
    other_settings = models.TextField(
        verbose_name="Advanced settings", blank=True,
        help_text=(
            'For advanced use cases, enter a JSON object with addtional configuration. '
            'The tpa-saml backend supports only {"requiredEntitlements": ["urn:..."]} '
            'which can be used to require the presence of a specific eduPersonEntitlement.'
        ))

    def clean(self):
        """ Standardize and validate fields """
        super(SAMLProviderConfig, self).clean()
        self.other_settings = clean_json(self.other_settings, dict)

    class Meta(object):
        verbose_name = "Provider Configuration (SAML IdP)"
        verbose_name_plural = "Provider Configuration (SAML IdPs)"

    def get_url_params(self):
        """ Get a dict of GET parameters to append to login links for this provider """
        return {'idp': self.idp_slug}

    def is_active_for_pipeline(self, pipeline):
        """ Is this provider being used for the specified pipeline? """
        return self.backend_name == pipeline['backend'] and self.idp_slug == pipeline['kwargs']['response']['idp_name']

    def match_social_auth(self, social_auth):
        """ Is this provider being used for this UserSocialAuth entry? """
        prefix = self.idp_slug + ":"
        return self.backend_name == social_auth.provider and social_auth.uid.startswith(prefix)

    def get_remote_id_from_social_auth(self, social_auth):
        """ Given a UserSocialAuth object, return the remote ID used by this provider. """
        assert self.match_social_auth(social_auth)
        # Remove the prefix from the UID
        return social_auth.uid[len(self.idp_slug) + 1:]

    def get_social_auth_uid(self, remote_id):
        """ Get social auth uid from remote id by prepending idp_slug to the remote id """
        return '{}:{}'.format(self.idp_slug, remote_id)

    def get_config(self):
        """
        Return a SAMLIdentityProvider instance for use by SAMLAuthBackend.

        Essentially this just returns the values of this object and its
        associated 'SAMLProviderData' entry.
        """
        if self.other_settings:
            conf = json.loads(self.other_settings)
        else:
            conf = {}
        attrs = (
            'attr_user_permanent_id', 'attr_full_name', 'attr_first_name',
            'attr_last_name', 'attr_username', 'attr_email', 'entity_id')
        for field in attrs:
            val = getattr(self, field)
            if val:
                conf[field] = val
        # Now get the data fetched automatically from the metadata.xml:
        data = SAMLProviderData.current(self.entity_id)
        if not data or not data.is_valid():
            log.error("No SAMLProviderData found for %s. Run 'manage.py saml pull' to fix or debug.", self.entity_id)
            raise AuthNotConfigured(provider_name=self.name)
        conf['x509cert'] = data.public_key
        conf['url'] = data.sso_url
        return SAMLIdentityProvider(self.idp_slug, **conf)


class SAMLConfiguration(ConfigurationModel):
    """
    General configuration required for this edX instance to act as a SAML
    Service Provider and allow users to authenticate via third party SAML
    Identity Providers (IdPs)
    """
    private_key = models.TextField(
        help_text=(
            'To generate a key pair as two files, run '
            '"openssl req -new -x509 -days 3652 -nodes -out saml.crt -keyout saml.key". '
            'Paste the contents of saml.key here. '
            'For increased security, you can avoid storing this in your database by leaving '
            'this field blank and setting it via the SOCIAL_AUTH_SAML_SP_PRIVATE_KEY setting '
            'in your instance\'s Django settings (or lms.auth.json).'
        ),
        blank=True,
    )
    public_key = models.TextField(
        help_text=(
            'Public key certificate. '
            'For increased security, you can avoid storing this in your database by leaving '
            'this field blank and setting it via the SOCIAL_AUTH_SAML_SP_PUBLIC_CERT setting '
            'in your instance\'s Django settings (or lms.auth.json).'
        ),
        blank=True,
    )
    entity_id = models.CharField(max_length=255, default="http://saml.example.com", verbose_name="Entity ID")
    org_info_str = models.TextField(
        verbose_name="Organization Info",
        default='{"en-US": {"url": "http://www.example.com", "displayname": "Example Inc.", "name": "example"}}',
        help_text="JSON dictionary of 'url', 'displayname', and 'name' for each language",
    )
    other_config_str = models.TextField(
        default='{\n"SECURITY_CONFIG": {"metadataCacheDuration": 604800, "signMetadata": false}\n}',
        help_text=(
            "JSON object defining advanced settings that are passed on to python-saml. "
            "Valid keys that can be set here include: SECURITY_CONFIG and SP_EXTRA"
        ),
    )

    class Meta(object):
        verbose_name = "SAML Configuration"
        verbose_name_plural = verbose_name

    def clean(self):
        """ Standardize and validate fields """
        super(SAMLConfiguration, self).clean()
        self.org_info_str = clean_json(self.org_info_str, dict)
        self.other_config_str = clean_json(self.other_config_str, dict)

        self.private_key = (
            self.private_key
            .replace("-----BEGIN RSA PRIVATE KEY-----", "")
            .replace("-----BEGIN PRIVATE KEY-----", "")
            .replace("-----END RSA PRIVATE KEY-----", "")
            .replace("-----END PRIVATE KEY-----", "")
            .strip()
        )
        self.public_key = (
            self.public_key
            .replace("-----BEGIN CERTIFICATE-----", "")
            .replace("-----END CERTIFICATE-----", "")
            .strip()
        )

    def get_setting(self, name):
        """ Get the value of a setting, or raise KeyError """
        if name == "ORG_INFO":
            return json.loads(self.org_info_str)
        if name == "SP_ENTITY_ID":
            return self.entity_id
        if name == "SP_PUBLIC_CERT":
            if self.public_key:
                return self.public_key
            # To allow instances to avoid storing keys in the DB, the key pair can also be set via Django:
            return getattr(settings, 'SOCIAL_AUTH_SAML_SP_PUBLIC_CERT', '')
        if name == "SP_PRIVATE_KEY":
            if self.private_key:
                return self.private_key
            # To allow instances to avoid storing keys in the DB, the private key can also be set via Django:
            return getattr(settings, 'SOCIAL_AUTH_SAML_SP_PRIVATE_KEY', '')
        other_config = json.loads(self.other_config_str)
        if name in ("TECHNICAL_CONTACT", "SUPPORT_CONTACT"):
            contact = {
                "givenName": "{} Support".format(settings.PLATFORM_NAME),
                "emailAddress": settings.TECH_SUPPORT_EMAIL
            }
            contact.update(other_config.get(name, {}))
            return contact
        return other_config[name]  # SECURITY_CONFIG, SP_EXTRA, or similar extra settings


class SAMLProviderData(models.Model):
    """
    Data about a SAML IdP that is fetched automatically by 'manage.py saml pull'

    This data is only required during the actual authentication process.
    """
    cache_timeout = 600
    fetched_at = models.DateTimeField(db_index=True, null=False)
    expires_at = models.DateTimeField(db_index=True, null=True)

    entity_id = models.CharField(max_length=255, db_index=True)  # This is the key for lookups in this table
    sso_url = models.URLField(verbose_name="SSO URL")
    public_key = models.TextField()

    class Meta(object):
        verbose_name = "SAML Provider Data"
        verbose_name_plural = verbose_name
        ordering = ('-fetched_at', )

    def is_valid(self):
        """ Is this data valid? """
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return bool(self.entity_id and self.sso_url and self.public_key)
    is_valid.boolean = True

    @classmethod
    def cache_key_name(cls, entity_id):
        """ Return the name of the key to use to cache the current data """
        return 'configuration/{}/current/{}'.format(cls.__name__, entity_id)

    @classmethod
    def current(cls, entity_id):
        """
        Return the active data entry, if any, otherwise None
        """
        cached = cache.get(cls.cache_key_name(entity_id))
        if cached is not None:
            return cached

        try:
            current = cls.objects.filter(entity_id=entity_id).order_by('-fetched_at')[0]
        except IndexError:
            current = None

        cache.set(cls.cache_key_name(entity_id), current, cls.cache_timeout)
        return current


class LTIProviderConfig(ProviderConfig):
    """
    Configuration required for this edX instance to act as a LTI
    Tool Provider and allow users to authenticate and be enrolled in a
    course via third party LTI Tool Consumers.
    """
    prefix = 'lti'
    backend_name = 'lti'
    icon_class = None  # This provider is not visible to users
    secondary = False  # This provider is not visible to users
    accepts_logins = False  # LTI login cannot be initiated by the tool provider
    KEY_FIELDS = ('lti_consumer_key', )

    lti_consumer_key = models.CharField(
        max_length=255,
        help_text=(
            'The name that the LTI Tool Consumer will use to identify itself'
        )
    )

    lti_hostname = models.CharField(
        max_length=255,
        help_text=(
            'The domain that  will be acting as the LTI consumer.'
        ),
        db_index=True
    )

    lti_consumer_secret = models.CharField(
        default=long_token,
        max_length=255,
        help_text=(
            'The shared secret that the LTI Tool Consumer will use to '
            'authenticate requests. Only this edX instance and this '
            'tool consumer instance should know this value. '
            'For increased security, you can avoid storing this in '
            'your database by leaving this field blank and setting '
            'SOCIAL_AUTH_LTI_CONSUMER_SECRETS = {"consumer key": "secret", ...} '
            'in your instance\'s Django setttigs (or lms.auth.json)'
        ),
        blank=True,
    )

    lti_max_timestamp_age = models.IntegerField(
        default=10,
        help_text=(
            'The maximum age of oauth_timestamp values, in seconds.'
        )
    )

    def match_social_auth(self, social_auth):
        """ Is this provider being used for this UserSocialAuth entry? """
        prefix = self.lti_consumer_key + ":"
        return self.backend_name == social_auth.provider and social_auth.uid.startswith(prefix)

    def get_remote_id_from_social_auth(self, social_auth):
        """ Given a UserSocialAuth object, return the remote ID used by this provider. """
        assert self.match_social_auth(social_auth)
        # Remove the prefix from the UID
        return social_auth.uid[len(self.lti_consumer_key) + 1:]

    def is_active_for_pipeline(self, pipeline):
        """ Is this provider being used for the specified pipeline? """
        try:
            return (
                self.backend_name == pipeline['backend'] and
                self.lti_consumer_key == pipeline['kwargs']['response'][LTI_PARAMS_KEY]['oauth_consumer_key']
            )
        except KeyError:
            return False

    def get_lti_consumer_secret(self):
        """ If the LTI consumer secret is not stored in the database, check Django settings instead """
        if self.lti_consumer_secret:
            return self.lti_consumer_secret
        return getattr(settings, 'SOCIAL_AUTH_LTI_CONSUMER_SECRETS', {}).get(self.lti_consumer_key, '')

    class Meta(object):
        verbose_name = "Provider Configuration (LTI)"
        verbose_name_plural = verbose_name


class ProviderApiPermissions(models.Model):
    """
    This model links OAuth2 client with provider Id.

    It gives permission for a OAuth2 client to access the information under certain IdPs.
    """
    client = models.ForeignKey(Client)
    provider_id = models.CharField(
        max_length=255,
        help_text=(
            'Uniquely identify a provider. This is different from backend_name.'
        )
    )

    class Meta(object):  # pylint: disable=missing-docstring
        verbose_name = "Provider API Permission"
        verbose_name_plural = verbose_name + 's'
