from openedx_events.learning.data import (
    CcxCourseData,
    CcxCoursePassingStatusData,
    CourseData,
    CoursePassingStatusData,
    UserData,
    UserPersonalData
)
from openedx_events.learning.signals import CCX_COURSE_PASSING_STATUS_UPDATED, COURSE_PASSING_STATUS_UPDATED


def emit_course_passing_status_update(user, course_id, is_passing):
    if hasattr(course_id, 'ccx'):
        CCX_COURSE_PASSING_STATUS_UPDATED.send_event(
            course_passing_status=CcxCoursePassingStatusData(
                is_passing=is_passing,
                user=UserData(
                    pii=UserPersonalData(
                        username=user.username,
                        email=user.email,
                        name=user.get_full_name(),
                    ),
                    id=user.id,
                    is_active=user.is_active,
                ),
                course=CcxCourseData(
                    ccx_course_key=course_id,
                    master_course_key=course_id.to_course_locator(),
                ),
            )
        )
    else:
        COURSE_PASSING_STATUS_UPDATED.send_event(
            course_passing_status=CoursePassingStatusData(
                is_passing=is_passing,
                user=UserData(
                    pii=UserPersonalData(
                        username=user.username,
                        email=user.email,
                        name=user.get_full_name(),
                    ),
                    id=user.id,
                    is_active=user.is_active,
                ),
                course=CourseData(
                    course_key=course_id,
                ),
            )
        )
