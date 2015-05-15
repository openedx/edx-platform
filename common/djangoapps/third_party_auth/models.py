"""
Models used to implement SAML SSO support in third_party_auth
(inlcuding Shibboleth support)
"""
from config_models.models import ConfigurationModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
import json
from social.backends.base import BaseAuth
from social.backends.oauth import BaseOAuth2
from social.backends.saml import SAMLAuth
from social.utils import module_member


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
_PSA_OAUTH2_BACKENDS = [backend_class.name for backend_class in _load_backend_classes(BaseOAuth2)]
_PSA_SAML_BACKENDS = [backend_class.name for backend_class in _load_backend_classes(SAMLAuth)]


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


class ProviderConfig(ConfigurationModel):
    """
    Abstract Base Class for configuring a third_party_auth provider
    """
    icon_class = models.CharField(max_length=50, default='fa-signin')
    name = models.CharField(max_length=50, blank=False)
    prefix = None  # used for provider_id. Set to a string value in subclass
    backend_name = None  # Set to a field or fixed value in subclass
    # "enabled" field is inherited from ConfigurationModel

    class Meta(object):  # pylint: disable=missing-docstring
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
    """
    prefix = 'oa2'
    KEY_FIELDS = ('backend_name', )  # Backend name is unique
    backend_name = models.CharField(
        max_length=50, choices=[(name, name) for name in _PSA_OAUTH2_BACKENDS], blank=False, db_index=True)
    key = models.TextField(blank=True)
    secret = models.TextField(blank=True)
    other_settings = models.TextField(blank=True)  # JSON field with other settings, if any. Usually blank.

    class Meta(object):  # pylint: disable=missing-docstring
        verbose_name = "Provider Configuration (OAuth2)"
        verbose_name_plural = verbose_name

    def clean(self):
        """ Standardize and validate fields """
        super(OAuth2ProviderConfig, self).clean()
        self.other_settings = clean_json(self.other_settings, dict)

    def get_setting(self, name):
        """ Get the value of a setting, or raise KeyError """
        if name in ("KEY", "SECRET"):
            return getattr(self, name.lower())
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
        max_length=50, default='tpa-saml', choices=[(name, name) for name in _PSA_SAML_BACKENDS], blank=False)
    idp_slug = models.SlugField(max_length=30, db_index=True)
    metadata_source = models.CharField(max_length=255, help_text="Generally this is a URL to a metadata XML file")
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

    class Meta(object):  # pylint: disable=missing-docstring
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


class SAMLConfiguration(ConfigurationModel):
    """
    General configuration required for this edX instance to act as a SAML
    Service Provider and allow users to authenticate via third party SAML
    Identity Providers (IdPs)
    """
    private_key = models.TextField()
    public_key = models.TextField()
    entity_id = models.CharField(max_length=255, default="http://saml.example.com")
    org_info_str = models.TextField(
        verbose_name="Organization Info",
        default='{"en-US": {"url": "http://www.example.com", "displayname": "Example Inc.", "name": "example"}}',
        help_text="JSON dictionary of 'url', 'displayname', and 'name' for each language",
    )
    other_config_str = models.TextField(
        default='{\n"SECURITY_CONFIG": {"metadataCacheDuration": 604800, "signMetadata": false}\n}')

    class Meta(object):  # pylint: disable=missing-docstring
        verbose_name = "SAML Configuration"
        verbose_name_plural = verbose_name

    def clean(self):
        """ Standardize and validate fields """
        super(SAMLConfiguration, self).clean()
        self.org_info_str = clean_json(self.org_info_str, dict)
        self.other_config_str = clean_json(self.other_config_str, dict)

    def get_setting(self, name):
        """ Get the value of a setting, or raise KeyError """
        if name == "ORG_INFO":
            return json.loads(self.org_info_str)
        if name == "SP_ENTITY_ID":
            return self.entity_id
        if name == "SP_PUBLIC_CERT":
            return self.public_key
        if name == "SP_PRIVATE_KEY":
            return self.private_key
        if name == "TECHNICAL_CONTACT":
            return {"givenName": "Technical Support", "emailAddress": settings.TECH_SUPPORT_EMAIL}
        if name == "SUPPORT_CONTACT":
            return {"givenName": "SAML Support", "emailAddress": settings.TECH_SUPPORT_EMAIL}
        other_config = json.loads(self.other_config_str)
        return other_config[name]  # SECURITY_CONFIG, SP_NAMEID_FORMATS, SP_EXTRA


class SAMLProviderData(ConfigurationModel):
    """
    Data about a SAML IdP that is generally fetched automatically.

    This data is only required during the actual authentication process.
    """
    KEY_FIELDS = ('idp_slug', )
    idp_slug = models.SlugField(max_length=30, db_index=True)
    entity_id = models.CharField(max_length=255)
    sso_url = models.URLField()
    public_key = models.TextField()

    class Meta(object):  # pylint: disable=missing-docstring
        verbose_name = "SAML Provider Data"
        verbose_name_plural = verbose_name
