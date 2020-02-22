"""
Contains configuration for schedules app
"""


from openedx.core.djangoapps.waffle_utils import (
    WaffleFlagNamespace, CourseWaffleFlag, WaffleFlag,
    WaffleSwitch, WaffleSwitchNamespace,
)

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'schedules')
WAFFLE_SWITCH_NAMESPACE = WaffleSwitchNamespace(name=u'schedules')

CREATE_SCHEDULE_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'create_schedules_for_course',
    flag_undefined_default=False
)

COURSE_UPDATE_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'send_updates_for_course',
    flag_undefined_default=False
)

DEBUG_MESSAGE_WAFFLE_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, u'enable_debugging')

COURSE_UPDATE_SHOW_UNSUBSCRIBE_WAFFLE_SWITCH = WaffleSwitch(WAFFLE_SWITCH_NAMESPACE, u'course_update_show_unsubscribe')
