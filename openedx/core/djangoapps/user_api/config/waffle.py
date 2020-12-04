"""
Waffle flags and switches to change user API functionality.
"""


from django.utils.translation import ugettext_lazy as _

from edx_toggles.toggles import WaffleSwitchNamespace

SYSTEM_MAINTENANCE_MSG = _(u'System maintenance in progress. Please try again later.')
WAFFLE_NAMESPACE = u'user_api'

# Switches
ENABLE_MULTIPLE_USER_ENTERPRISES_FEATURE = u'enable_multiple_user_enterprises_feature'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for user_api.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'UserAPI: ')
