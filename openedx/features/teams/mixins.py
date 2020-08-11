from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser


class AllowInActiveUserAuthMixin(object):
    """
    OAuth2AuthenticationAllowInactiveUser must come first to return a 401 for unauthenticated users
    use OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser instead of
    OAuth2Authentication, SessionAuthentication to allow access to inactive user
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
