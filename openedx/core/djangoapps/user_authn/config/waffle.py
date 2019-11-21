"""
Waffle flags and switches for user authn.
"""
from __future__ import absolute_import

from openedx.core.djangoapps.waffle_utils import WaffleSwitch, WaffleSwitchNamespace

_WAFFLE_NAMESPACE = u'user_authn'
_WAFFLE_SWITCH_NAMESPACE = WaffleSwitchNamespace(name=_WAFFLE_NAMESPACE, log_prefix=u'UserAuthN: ')

# .. toggle_name: user_authn.enable_login_using_thirdparty_auth_only
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, users must be sign in using their allowed domain SSO account.
# .. toggle_category: authn
# .. toggle_use_cases: incremental_release
# .. toggle_creation_date: 2019-11-20
# .. toggle_expiration_date: 2020-01-31
# .. toggle_warnings: Requires THIRD_PARTY_AUTH_ONLY_DOMAIN to also be set.
# .. toggle_tickets: ENT-2461
# .. toggle_status: supported
ENABLE_LOGIN_USING_THIRDPARTY_AUTH_ONLY = WaffleSwitch(
    _WAFFLE_SWITCH_NAMESPACE, 'enable_login_using_thirdparty_auth_only'
)

# .. toggle_name: user_authn.update_login_user_error_status_code
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Changes auth failures (non-SSO) from 200 to 400.
# .. toggle_category: authn
# .. toggle_use_cases: incremental_release
# .. toggle_creation_date: 2019-11-21
# .. toggle_expiration_date: 2020-01-31
# .. toggle_warnings: Causes backward incompatible change. Document before removing.
# .. toggle_tickets: ARCH-1253
# .. toggle_status: supported
UPDATE_LOGIN_USER_ERROR_STATUS_CODE = WaffleSwitch(
    _WAFFLE_SWITCH_NAMESPACE, 'update_login_user_error_status_code'
)
