"""
Toggles for the User Tours Experience.
"""

from edx_toggles.toggles import WaffleFlag

# .. toggle_name: user_tours.tours_enabled
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of user tours in the LMS.
# .. toggle_warnings: None
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-11-19
# .. toggle_target_removal_date: 2022-02-14
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-1026
USER_TOURS_ENABLED = WaffleFlag('user_tours.tours_enabled', module_name=__name__, log_prefix='user_tours')
