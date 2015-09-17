"""
A custom Strategy for python-social-auth that allows us to fetch configuration from
ConfigurationModels rather than django.settings
"""
import logging
from .models import OAuth2ProviderConfig
from .pipeline import AUTH_ENTRY_CUSTOM
from social.backends.oauth import OAuthAuth
from social.strategies.django_strategy import DjangoStrategy


log = logging.getLogger(__name__)


class ConfigurationModelStrategy(DjangoStrategy):
    """
    A DjangoStrategy customized to load settings from ConfigurationModels
    for upstream python-social-auth backends that we cannot otherwise modify.
    """
    def setting(self, name, default=None, backend=None):
        """
        Load the setting from a ConfigurationModel if possible, or fall back to the normal
        Django settings lookup.

        OAuthAuth subclasses will call this method for every setting they want to look up.
        SAMLAuthBackend subclasses will call this method only after first checking if the
            setting 'name' is configured via SAMLProviderConfig.
        LTIAuthBackend subclasses will call this method only after first checking if the
            setting 'name' is configured via LTIProviderConfig.
        """
        if isinstance(backend, OAuthAuth):
            provider_config = OAuth2ProviderConfig.current(backend.name)
            if not provider_config.enabled:
                raise Exception("Can't fetch setting of a disabled backend/provider.")
            try:
                return provider_config.get_setting(name)
            except KeyError:
                pass

        # special case handling of login error URL if we're using a custom auth entry point:
        if name == 'LOGIN_ERROR_URL':
            auth_entry = self.request.session.get('auth_entry')
            if auth_entry and auth_entry in AUTH_ENTRY_CUSTOM:
                error_url = AUTH_ENTRY_CUSTOM[auth_entry].get('error_url')
                if error_url:
                    return error_url

        # At this point, we know 'name' is not set in a [OAuth2|LTI|SAML]ProviderConfig row.
        # It's probably a global Django setting like 'FIELDS_STORED_IN_SESSION':
        return super(ConfigurationModelStrategy, self).setting(name, default, backend)

    def _ensure_passes_length_check(self, user_data, key, fallback, min_length=2):
        """
        Ensures that value we get from user_data is meets length requirements. IF it is shorter than required, fallback
        is used
        """
        assert len(fallback) >= min_length
        value = user_data.get(key)
        if value and len(value) >= min_length:
            return value
        return fallback

    def create_user(self, *args, **kwargs):
        """
        # Creates user using information provided by pipeline. This method is called in create_user pipeline step.
        # Unless the workflow is changed, create_user immediately terminates if the user already found/
        # So far, user is either created in ensure_user_information via registration form or account needs to be
        # autoprovisioned. So, this method is only called when autoprovisioning account.
        """
        from student.views import create_account_with_params
        from .pipeline import make_random_password

        user_fields = dict(kwargs)
        # needs to be >2 chars to pass validation
        name = self._ensure_passes_length_check(
            user_fields, 'fullname', self.setting("THIRD_PARTY_AUTH_FALLBACK_FULL_NAME")
        )
        password = self._ensure_passes_length_check(user_fields, 'password', make_random_password())

        user_fields['name'] = name
        user_fields['password'] = password
        user_fields['honor_code'] = True
        user_fields['terms_of_service'] = True

        if not user_fields.get('email'):
            user_fields['email'] = "{username}@{domain}".format(
                username=user_fields['username'], domain=self.setting("FAKE_EMAIL_DOMAIN")
            )

        # when autoprovisioning we need to skip email activation, hence skip_email is True
        return create_account_with_params(self.request, user_fields, skip_email=True)

    def request_host(self):
        """
        Host in use for this request
        """
        # TODO: this override is a temporary measure until upstream python-social-auth patch is merged:
        # https://github.com/omab/python-social-auth/pull/741
        if self.setting('RESPECT_X_FORWARDED_HEADERS', False):
            forwarded_host = self.request.META.get('HTTP_X_FORWARDED_HOST')
            if forwarded_host:
                return forwarded_host

        return super(ConfigurationModelStrategy, self).request_host()

    def request_port(self):
        """
        Port in use for this request
        """
        # TODO: this override is a temporary measure until upstream python-social-auth patch is merged:
        # https://github.com/omab/python-social-auth/pull/741
        if self.setting('RESPECT_X_FORWARDED_HEADERS', False):
            forwarded_port = self.request.META.get('HTTP_X_FORWARDED_PORT')
            if forwarded_port:
                return forwarded_port

        return super(ConfigurationModelStrategy, self).request_port()
