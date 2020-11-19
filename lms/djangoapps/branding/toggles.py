"""
Waffle flags for Branding app.
"""
from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace


WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='branding')
# Waffle flag for testing purpose only. When setting the flag in prod,
# make sure to have the following settings. Use "dwft_branding.enable_branding_logs=1"
# in the browser query to enable the flag.
# .. toggle_name: branding.enable_branding_logs
# .. toggle_everyone: unknown
# .. toggle_testing: True
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports testing for re-branding work.
# .. toggle_category: branding
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-11-22
# .. toggle_target_removal_date: 2021-01-01
# .. toggle_warnings: n/a
# .. toggle_tickets: TNL-7695
# .. toggle_status: supported
ENABLE_BRANDING_LOGS = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='enable_branding_logs',
)


def app_logs_enabled():
    """Check if app logging is enabled. """
    return ENABLE_BRANDING_LOGS.is_enabled()
