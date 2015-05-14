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
_PSA_OAUTH2_BACKENDS = {backend_class.name: backend_class for backend_class in _load_backend_classes(BaseOAuth2)}
_PSA_SAML_BACKENDS = {backend_class.name: backend_class for backend_class in _load_backend_classes(SAMLAuth)}


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
    backend_name = None  # Set to a field or fixed value in subclass
    # "enabled" field is inherited from ConfigurationModel

    class Meta(object):  # pylint: disable=missing-docstring
        abstract = True


class OAuth2ProviderConfig(ProviderConfig):
    """
    Configuration Entry for an OAuth2 based provider.
    """
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


class SAMLProviderConfig(ProviderConfig):
    """
    Configuration Entry for a SAML/Shibboleth provider.
    """
    KEY_FIELDS = ('idp_slug', )
    backend_name = models.CharField(
        max_length=50, default='tpa-saml', choices=[(name, name) for name in _PSA_SAML_BACKENDS], blank=False)
    idp_slug = models.SlugField(max_length=30, db_index=True)
    metadata_source = models.CharField(max_length=255, help_text="Generally this is a URL to a metadata XML file")
    attr_user_permanent_id = models.CharField(max_length=128)
    attr_full_name = models.CharField(max_length=128)
    attr_first_name = models.CharField(max_length=128)
    attr_last_name = models.CharField(max_length=128)
    attr_username = models.CharField(max_length=128)
    attr_email = models.CharField(max_length=128)

    class Meta(object):  # pylint: disable=missing-docstring
        verbose_name = "Provider Configuration (SAML IdP)"
        verbose_name_plural = "Provider Configuration (SAML IdPs)"


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
