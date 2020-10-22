"""
Waffle flags and switches to change user API functionality.
"""
from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace, WaffleFlagNamespace, WaffleFlag

SYSTEM_MAINTENANCE_MSG = _(u'System maintenance in progress. Please try again later.')
WAFFLE_NAMESPACE = u'user_api'
_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(WAFFLE_NAMESPACE)
PASSWORD_UNICODE_NORMALIZE_FLAG = WaffleFlag(_WAFFLE_FLAG_NAMESPACE, u'password_unicode_normalize')

# Switches
PREVENT_AUTH_USER_WRITES = u'prevent_auth_user_writes'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for user_api.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'UserAPI: ')
