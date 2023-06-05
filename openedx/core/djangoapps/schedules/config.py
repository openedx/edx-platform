"""
Contains configuration for schedules app
"""


from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace, WaffleSwitch, WaffleSwitchNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='schedules')
WAFFLE_SWITCH_NAMESPACE = WaffleSwitchNamespace(name='schedules')

CREATE_SCHEDULE_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='create_schedules_for_course',
    module_name=__name__,
)

COURSE_UPDATE_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='send_updates_for_course',
    module_name=__name__,
)

DEBUG_MESSAGE_WAFFLE_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'enable_debugging', __name__)

COURSE_UPDATE_SHOW_UNSUBSCRIBE_WAFFLE_SWITCH = WaffleSwitch(
    WAFFLE_SWITCH_NAMESPACE,
    'course_update_show_unsubscribe',
    __name__
)
