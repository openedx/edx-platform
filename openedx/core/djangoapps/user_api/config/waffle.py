"""
Waffle flags and switches to change user API functionality.
"""


from django.utils.translation import ugettext_lazy as _

from edx_toggles.toggles import WaffleSwitch

SYSTEM_MAINTENANCE_MSG = _(u'System maintenance in progress. Please try again later.')

# .. toggle_name: user_api.enable_multiple_user_enterprises_feature
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: If enabled then learners linked to multiple enterprises will be asked to select default
#   enterprise for current session.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2019-11-01
# .. toggle_target_removal_date: 2021-06-01
# .. toggle_tickets: ENT-2339, ENT-4041
ENABLE_MULTIPLE_USER_ENTERPRISES_FEATURE = WaffleSwitch(
    'user_api.enable_multiple_user_enterprises_feature', __name__
)
