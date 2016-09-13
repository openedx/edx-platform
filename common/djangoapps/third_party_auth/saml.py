"""
Slightly customized python-social-auth backend for SAML 2.0 support
"""
import logging
from django.http import Http404
from django.utils.functional import cached_property
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
        try:
            return self._config.get_setting(name)
        except KeyError:
            return self.strategy.setting(name, default)

    def auth_url(self):
        """
        Check that SAML is enabled and that the request includes an 'idp'
        parameter before getting the URL to which we must redirect in order to
        authenticate the user.

        raise Http404 if SAML authentication is disabled.
        raise AuthMissingParameter if the 'idp' parameter is missing.
        """
        if not self._config.enabled:
            log.error('SAML authentication is not enabled')
            raise Http404
        # TODO: remove this check once the fix is merged upstream:
        # https://github.com/omab/python-social-auth/pull/821
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

    def _create_saml_auth(self, idp):
        """
        Get an instance of OneLogin_Saml2_Auth

        idp: The Identity Provider - a social.backends.saml.SAMLIdentityProvider instance
        """
        # We only override this method so that we can add extra debugging when debug_mode is True
        # Note that auth_inst is instantiated just for the current HTTP request, then is destroyed
        auth_inst = super(SAMLAuthBackend, self)._create_saml_auth(idp)
        from .models import SAMLProviderConfig
        if SAMLProviderConfig.current(idp.name).debug_mode:

            def wrap_with_logging(method_name, action_description, xml_getter):
                """ Wrap the request and response handlers to add debug mode logging """
                method = getattr(auth_inst, method_name)

                def wrapped_method(*args, **kwargs):
                    """ Wrapped login or process_response method """
                    result = method(*args, **kwargs)
                    log.info("SAML login %s for IdP %s. XML is:\n%s", action_description, idp.name, xml_getter())
                    return result
                setattr(auth_inst, method_name, wrapped_method)

            wrap_with_logging("login", "request", auth_inst.get_last_request_xml)
            wrap_with_logging("process_response", "response", auth_inst.get_last_response_xml)

        return auth_inst

    @cached_property
    def _config(self):
        from .models import SAMLConfiguration
        return SAMLConfiguration.current()
