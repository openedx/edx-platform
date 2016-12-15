"""
Slightly customized python-social-auth backend for SAML 2.0 support
"""
import logging
from social.backends.saml import SAMLAuth, OID_EDU_PERSON_ENTITLEMENT
from social.exceptions import AuthForbidden, AuthMissingParameter

log = logging.getLogger(__name__)


class SAMLAuthBackend(SAMLAuth):  # pylint: disable=abstract-method
    """
    Customized version of SAMLAuth that gets the list of IdPs from third_party_auth's list of
    enabled providers.
    """
    name = "tpa-saml"

    def get_idp(self, idp_name):
        """ Given the name of an IdP, get a SAMLIdentityProvider instance """
        from .models import SAMLProviderConfig
        return SAMLProviderConfig.current(idp_name).get_config()

    def setting(self, name, default=None):
        """ Get a setting, from SAMLConfiguration """
        if not hasattr(self, '_config'):
            from .models import SAMLConfiguration
            self._config = SAMLConfiguration.current()  # pylint: disable=attribute-defined-outside-init
        if not self._config.enabled:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured("SAML Authentication is not enabled.")
        try:
            return self._config.get_setting(name)
        except KeyError:
            return self.strategy.setting(name, default)

    def auth_url(self):
        """
        Check that the request includes an 'idp' parameter before getting the
        URL to which we must redirect in order to authenticate the user.

        raise AuthMissingParameter if the 'idp' parameter is missing.

        TODO: remove this method once the fix is merged upstream:
        https://github.com/omab/python-social-auth/pull/821
        """
        if 'idp' not in self.strategy.request_data():
            raise AuthMissingParameter(self, 'idp')
        return super(SAMLAuthBackend, self).auth_url()

    def _check_entitlements(self, idp, attributes):
        """
        Check if we require the presence of any specific eduPersonEntitlement.

        raise AuthForbidden if the user should not be authenticated, or do nothing
        to allow the login pipeline to continue.
        """
        if "requiredEntitlements" in idp.conf:
            entitlements = attributes.get(OID_EDU_PERSON_ENTITLEMENT, [])
            for expected in idp.conf['requiredEntitlements']:
                if expected not in entitlements:
                    log.warning(
                        "SAML user from IdP %s rejected due to missing eduPersonEntitlement %s", idp.name, expected)
                    raise AuthForbidden(self)
