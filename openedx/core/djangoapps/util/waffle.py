"""
Waffle flags and switches
"""


from edx_toggles.toggles import LegacyWaffleSwitchNamespace

WAFFLE_NAMESPACE = u'open_edx_util'

# Switches
DISPLAY_MAINTENANCE_WARNING = u'display_maintenance_warning'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for open_edx_util.
    """
    return LegacyWaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'OpenEdX Util: ')
