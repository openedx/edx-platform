from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, CourseWaffleFlag, WaffleFlag


WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'schedules')

COURSE_UPDATE_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'send_updates_for_course',
    flag_undefined_default=False
)

DEBUG_MESSAGE_WAFFLE_FLAG = WaffleFlag(WAFFLE_FLAG_NAMESPACE, u'enable_debugging')
