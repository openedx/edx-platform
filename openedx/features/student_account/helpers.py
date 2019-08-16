from datetime import datetime

from lms.djangoapps.philu_overrides.constants import ACTIVATION_ALERT_TYPE
from pytz import utc

from constants import NON_ACTIVE_COURSE_NOTIFICATION
from student.models import CourseEnrollment
from courseware.models import StudentModule
from openedx.features.course_card.helpers import get_course_open_date
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link


def get_non_active_course(user):
    DAYS_TO_DISPLAY_NOTIFICATION = 7

    all_user_courses = CourseEnrollment.objects.filter(user=user, is_active=True)

    non_active_courses = []
    non_active_course_info = []

    for user_course in all_user_courses:

        today = datetime.now(utc).date()

        try:
            course = CourseOverview.objects.get(id=user_course.course_id, end__gte=today)
        except CourseOverview.DoesNotExist:
            continue

        course_start_date = get_course_open_date(course).date()
        delta_date = today - course_start_date

        if delta_date.days >= DAYS_TO_DISPLAY_NOTIFICATION:

            modules = StudentModule.objects.filter(course_id=course.id, student_id=user.id,
                                                   created__gt=course_start_date)

            # Make this check equals to zero to make it more generic.
            if len(modules) <= 0:
                non_active_courses.append(course)

    if len(non_active_courses) > 0:
        error = NON_ACTIVE_COURSE_NOTIFICATION % (non_active_courses[0].display_name,
                                                  get_course_first_chapter_link(course=non_active_courses[0]))
        non_active_course_info.append({"type": ACTIVATION_ALERT_TYPE,
                                       "alert": error})
    return non_active_course_info
