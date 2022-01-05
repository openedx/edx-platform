"""
Utility functions for third_party_auth
"""

import datetime
from uuid import UUID

import dateutil.parser
import pytz
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from enterprise.models import EnterpriseCustomerIdentityProvider, EnterpriseCustomerUser
from lxml import etree
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from social_core.pipeline.social_auth import associate_by_email

from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
from openedx.core.djangolib.markup import Text

from . import provider

SAML_XML_NS = 'urn:oasis:names:tc:SAML:2.0:metadata'  # The SAML Metadata XML namespace


class MetadataParseError(Exception):
    """ An error occurred while parsing the SAML metadata from an IdP """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


def parse_metadata_xml(xml, entity_id):
    """
    Given an XML document containing SAML 2.0 metadata, parse it and return a tuple of
    (public_key, sso_url, expires_at) for the specified entityID.

    Raises MetadataParseError if anything is wrong.
    """

    if xml.tag == etree.QName(SAML_XML_NS, 'EntityDescriptor'):
        entity_desc = xml
    else:
        if xml.tag != etree.QName(SAML_XML_NS, 'EntitiesDescriptor'):
            raise MetadataParseError(Text("Expected root element to be <EntitiesDescriptor>, not {}").format(xml.tag))
        entity_desc = xml.find(
            ".//{}[@entityID='{}']".format(etree.QName(SAML_XML_NS, 'EntityDescriptor'), entity_id)
        )
        if entity_desc is None:
            raise MetadataParseError(f"Can't find EntityDescriptor for entityID {entity_id}")

    expires_at = None
    if "validUntil" in xml.attrib:
        expires_at = dateutil.parser.parse(xml.attrib["validUntil"])
    if "cacheDuration" in xml.attrib:
        cache_expires = OneLogin_Saml2_Utils.parse_duration(xml.attrib["cacheDuration"])
        cache_expires = datetime.datetime.fromtimestamp(cache_expires, tz=pytz.utc)
        if expires_at is None or cache_expires < expires_at:
            expires_at = cache_expires

    sso_desc = entity_desc.find(etree.QName(SAML_XML_NS, "IDPSSODescriptor"))
    if sso_desc is None:
        raise MetadataParseError("IDPSSODescriptor missing")
    if 'urn:oasis:names:tc:SAML:2.0:protocol' not in sso_desc.get("protocolSupportEnumeration"):
        raise MetadataParseError("This IdP does not support SAML 2.0")

    # Now we just need to get the public_key and sso_url
    # We want the use='signing' cert, not the 'encryption' one
    public_key = sso_desc.findtext("./{}[@use='signing']//{}".format(
        etree.QName(SAML_XML_NS, "KeyDescriptor"), "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"
    ))
    if not public_key:
        # it's possible that there is just one keyDescription with no use attribute
        # that is a shortcut for both signing and encryption combined. So we can use that as fallback.
        public_key = sso_desc.findtext("./{}//{}".format(
            etree.QName(SAML_XML_NS, "KeyDescriptor"), "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"
        ))
        if not public_key:
            raise MetadataParseError("Public Key missing. Expected an <X509Certificate>")
    public_key = public_key.replace(" ", "")
    binding_elements = sso_desc.iterfind("./{}".format(etree.QName(SAML_XML_NS, "SingleSignOnService")))
    sso_bindings = {element.get('Binding'): element.get('Location') for element in binding_elements}
    try:
        # The only binding supported by python-saml and python-social-auth is HTTP-Redirect:
        sso_url = sso_bindings['urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']
    except KeyError:
        raise MetadataParseError("Unable to find SSO URL with HTTP-Redirect binding.")  # lint-amnesty, pylint: disable=raise-missing-from
    return public_key, sso_url, expires_at


def user_exists(details):
    """
    Return True if user with given details exist in the system.

    Arguments:
        details (dict): dictionary containing user infor like email, username etc.

    Returns:
        (bool): True if user with given details exists, `False` otherwise.
    """
    user_queryset_filter = {}
    email = details.get('email')
    username = details.get('username')
    if email:
        user_queryset_filter['email'] = email
    elif username:
        user_queryset_filter['username__iexact'] = username

    if user_queryset_filter:
        return User.objects.filter(**user_queryset_filter).exists()

    return False


def get_user_from_email(details):
    """
    Return user with given details exist in the system.∂i

    Arguments:
        details (dict): dictionary containing user email.

    Returns:
        User: if user with given details exists, None otherwise.
    """
    email = details.get('email')
    if email:
        return User.objects.filter(email=email).first()

    return None


def convert_saml_slug_provider_id(provider):  # lint-amnesty, pylint: disable=redefined-outer-name
    """
    Provider id is stored with the backend type prefixed to it (ie "saml-")
    Slug is stored without this prefix.
    This just converts between them whenever you expect the opposite of what you currently have.

    Arguments:
        provider (string): provider_id or slug

    Returns:
        (string): Opposite of what you inputted (slug -> provider_id; provider_id -> slug)
    """
    if provider.startswith('saml-'):
        return provider[5:]
    else:
        return 'saml-' + provider


def validate_uuid4_string(uuid_string):
    """
    Returns True if valid uuid4 string, or False
    """
    try:
        UUID(uuid_string, version=4)
    except ValueError:
        return False
    return True


def is_saml_provider(backend, kwargs):
    """ Verify that the third party provider uses SAML """
    current_provider = provider.Registry.get_from_pipeline({'backend': backend, 'kwargs': kwargs})
    saml_providers_list = list(provider.Registry.get_enabled_by_backend_name('tpa-saml'))
    return (current_provider and
            current_provider.slug in [saml_provider.slug for saml_provider in saml_providers_list]), current_provider


def is_enterprise_customer_user(provider_id, user):
    """ Verify that the user linked to enterprise customer of current identity provider"""
    enterprise_idp = EnterpriseCustomerIdentityProvider.objects.get(provider_id=provider_id)

    return EnterpriseCustomerUser.objects.filter(enterprise_customer=enterprise_idp.enterprise_customer,
                                                 user_id=user.id).exists()


def is_oauth_provider(backend_name, **kwargs):
    """
    Verify that the third party provider uses oauth
    """
    current_provider = provider.Registry.get_from_pipeline({'backend': backend_name, 'kwargs': kwargs})
    if current_provider:
        return current_provider.provider_id.startswith(OAuth2ProviderConfig.prefix)

    return False


def get_associated_user_by_email_response(backend, details, user, *args, **kwargs):
    """
    Gets the user associated by the `associate_by_email` social auth method
    """

    association_response = associate_by_email(backend, details, user, *args, **kwargs)

    if (
        association_response and
        association_response.get('user')
    ):
        # Only return the user matched by email if their email has been activated.
        # Otherwise, an illegitimate user can create an account with another user's
        # email address and the legitimate user would now login to the illegitimate
        # account.
        return (association_response, association_response['user'].is_active)

    return (None, False)
