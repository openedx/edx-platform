"""
Waffle flags and switches for user tahoe sites.
"""


from openedx.core.djangoapps.waffle_utils import WaffleSwitch, WaffleSwitchNamespace

_WAFFLE_NAMESPACE = u'openedx_core_tahoe_sites'
_WAFFLE_SWITCH_NAMESPACE = WaffleSwitchNamespace(name=_WAFFLE_NAMESPACE, log_prefix=u'Tahoe Sites (Open edX Core): ')

ENABLE_CONFIG_VALUES_MODIFIER = WaffleSwitch(
    _WAFFLE_SWITCH_NAMESPACE, 'enable_configuration_values_modifier'
)
