from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlagNamespace

WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'instructor_dashboard')
ENABLE_COMMUNICATOR_WAFFLE_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'enable_communicator',
    flag_undefined_default=False
)

COMMUNICATOR_BACKEND_URL = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'communicator_backend_url',
    flag_undefined_default=False
)