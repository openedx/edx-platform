"""
Waffle flags and switches for user authn.
"""
from __future__ import absolute_import

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

WAFFLE_NAMESPACE = u'user_authn'

# If this switch is enabled then users must be sign in using their allowed domain SSO account
ENABLE_LOGIN_USING_THIRDPARTY_AUTH_ONLY = 'enable_login_using_thirdparty_auth_only'

waffle = WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'UserAuthN: ')
