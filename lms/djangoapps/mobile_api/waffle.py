"""
This module contains various configuration settings via
waffle switches for mobile apps.
"""

from edx_toggles.toggles import WaffleFlag

# .. toggle_name: mobile.value_prop_enabled
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable value props on mobile apps for mobile users
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2022-06-13
# .. toggle_target_removal_date: None
# .. toggle_warnings: When the flag is ON,
# .. toggle_tickets: https://2u-internal.atlassian.net/browse/LEARNER-8864
VALUE_PROP_ENABLED = WaffleFlag(
    'mobile.value_prop_enabled',
    __name__,
)
